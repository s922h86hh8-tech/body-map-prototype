#!/usr/bin/env python3
"""Playwright checks on GENERATED SYNTHETIC pixels. No real CT or patient imagery."""
import base64
import io
import json
import tempfile
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/'l3-verse-orientation-review-v7.3.html'
N=101

def fake_png():
    image=Image.new('RGB',(N,N),color=(70,90,110))
    b=io.BytesIO();image.save(b,format='PNG')
    return base64.b64encode(b.getvalue()).decode('ascii')

def fake_review_file(destination):
    png=fake_png()
    basis={'axial':([1,0,0],[0,1,0],'R','A'),
           'coronal':([1,0,0],[0,0,1],'R','S'),
           'sagittal':([0,1,0],[0,0,1],'A','S')}
    screens={name:{
      'pixel_right_ras':x,'pixel_up_ras':y,'right_edge':right,'top_edge':top,
      'ct_png_base64':png,'ct_l3_overlay_png_base64':png,
      'source_CT_plane_inside_fraction':1.0,'l3_pixels_in_plane':400
    } for name,(x,y,right,top) in basis.items()}
    result={
      'schema':'L3_VERSE_ORIENTATION_REVIEW_V7_3_LOCAL_ONLY',
      'anatomy_approved':False,'case_id_local':'SYNTHETIC_BROWSER_TEST',
      'source_CT_sha256':'a'*64,'source_mask_sha256':'b'*64,
      'label22_source_voxels':600,'center_world_ras_mm':[0,0,0],
      'view_pixels_each_side':N,'pitch_mm_per_pixel':1.0,'screens':screens,
      'images_are_sensitive_do_not_upload':True
    }
    destination.write_text(json.dumps(result),encoding='utf-8')

def main():
    with tempfile.TemporaryDirectory() as t, sync_playwright() as pw:
        src=Path(t)/'SYNTHETIC_REVIEW.json';fake_review_file(src)
        browser=pw.chromium.launch(headless=True)
        for width in (320,390,768):
            page=browser.new_page(viewport={'width':width,'height':844},accept_downloads=True)
            page.goto(HTML.as_uri(),wait_until='load')
            assert page.locator('#localFile').count()==1
            page.locator('#localFile').set_input_files(str(src))
            page.wait_for_function('document.getElementById("sagittalImg").complete && document.getElementById("sagittalImg").naturalWidth===101')
            assert not page.locator('#sagittalEmpty').is_visible()
            assert not page.locator('#axialEmpty').is_visible()
            assert not page.locator('#coronalEmpty').is_visible()
            assert 'SYNTHETIC_BROWSER_TEST' in page.locator('#sourceInfo').inner_text()
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth+1'),f'overflow {width}'
            rect=page.locator('#sagittalImg').bounding_box()
            assert rect
            page.locator('#sagittalImg').click(position={'x':rect['width']*.75,'y':rect['height']*.50})
            page.locator('#landmarkKind').select_option('spinous_posterior')
            page.locator('#sagittalImg').click(position={'x':rect['width']*.25,'y':rect['height']*.50})
            assert '数値上の前後順序は＋A方向と一致' in page.locator('#result').inner_text(), (width,page.locator('#result').inner_text(),page.locator('#marks').inner_text())
            assert page.locator('#sagittalMarks .marker').count()==2
            page.locator('#showCT').click()
            assert page.locator('#showCT').get_attribute('aria-pressed')=='true'
            with page.expect_download() as info:
                page.locator('#export').click()
            output=info.value
            assert output.suggested_filename.endswith('LOCAL.json')
            downloaded=json.loads(Path(output.path()).read_text(encoding='utf-8'))
            assert downloaded['expert_anatomy_approved'] is False
            assert downloaded['numeric_ap_screen']['status']=='numeric_expected_order'
            assert len(downloaded['items'])==2
            page.locator('#clear').click()
            assert page.locator('#export').is_disabled()
            assert page.locator('#sagittalEmpty').is_visible()
            page.close()
            print('L3_V73_SYNTHETIC_BROWSER_PASS '+json.dumps({'width':width,'no_horizontal_scroll':True,'landmark_click':True,'local_export':True,'anatomy_approved':False}))
        browser.close()

if __name__=='__main__':main()
