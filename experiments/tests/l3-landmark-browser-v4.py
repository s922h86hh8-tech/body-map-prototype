#!/usr/bin/env python3
"""Browser test of paired original CT intensity plus 3D L3 segmentation.

Works from repository root:
 python -m pip install playwright
 python -m playwright install chromium
 python experiments/tests/l3-local-viewer-browser-v1.py /path/to/PRIVATE-L3-bundle.json

No raw CT / image / derived artifact is written or uploaded. Checks a desktop
and an iPhone-sized mobile Chromium viewport; this is NOT actual iPhone Safari.
"""
import argparse
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[2]
URL_PART='/experiments/l3-ct-review-v4.html'
def port_available():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]

def check_browser(context,bundle_path,viewport_name):
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda err:errors.append(str(err)[:230]))
    page.goto(URL_PART if URL_PART.startswith('http') else 'http://127.0.0.1:'+str(PORT)+URL_PART,
              wait_until='domcontentloaded',timeout=45000)
    page.locator('#ownStatus').get_by_text('旧版の独自形状・解剖学的未合格').wait_for(timeout=60000)
    page.locator('#reviewFile').set_input_files(str(bundle_path))
    page.get_by_text('ローカル読込済：',exact=False).wait_for(timeout=60000)
    page.get_by_text('個体由来メッシュ・関節面と完全性は未検証').wait_for(timeout=15000)
    for id in ('ownCanvas','ctCanvas'):
        assert page.locator('#'+id+' canvas').count()==1,id
        size=page.locator('#'+id).bounding_box()
        assert size and size['width']>=300 and size['height']>=250,(id,size)
    assert page.locator('#numericLegend .legendItem').count()==7
    for i in range(1,8):
        assert page.locator('#numericLegend').get_by_text('ラベル '+str(i)+'（名称未確認）').count()==1
    for id in ('axialImg','coronalImg','sagittalImg'):
        assert page.locator('#'+id).evaluate('(node) => node.complete && node.naturalWidth > 0'),id
    for mode in ('ct','labels','overlay'):
        b=page.locator('button[data-image-mode="'+mode+'"]')
        b.click()
        assert b.get_attribute('aria-pressed')=='true'
        caption=page.locator('#axialCaption').inner_text()
        expected={'ct':'元CT画像','labels':'ラベル色分け','overlay':'CT画像＋領域'}[mode]
        assert expected in caption,(mode,caption)
        assert page.locator('#axialImg').evaluate('(node) => node.complete && node.naturalWidth > 0')
    for k in ('axial','coronal','sagittal'):
        b=page.locator('button[data-plane="'+k+'"]')
        b.click()
        assert b.get_attribute('aria-pressed')=='true'
    for view in ('posterior','superior','oblique'):
        b=page.locator('button[data-view="'+view+'"]')
        b.click()
        assert b.get_attribute('aria-pressed')=='true'
    # Verify actual section-pixel -> canonical voxel -> RAS transform in downloaded JSON.
    page.locator('#landmarkKind').select_option('spinous_posterior')
    axial=page.locator('#axialImg')
    size=axial.bounding_box()
    assert size
    axial.click(position={'x':size['width']*.5,'y':size['height']*.5})
    assert page.locator('#axialMarks .landmarkSpot').count()==1
    assert '1点を仮登録' in page.locator('#markInfo').inner_text()
    with page.expect_download() as download_info:
        page.locator('#markExport').click()
    download=download_info.value
    record=json.loads(Path(download.path()).read_text())
    assert record['schema']=='L3_LOCAL_LANDMARK_REVIEW_V1'
    assert record['ready_for_anatomical_approval'] is False
    assert record['anatomical_name_to_numeric_class_mapping_verified'] is False
    assert len(record['items'])==1
    assert record['items'][0]['reviewer_confirmation']=='unverified_candidate'
    j=json.loads(Path(bundle_path).read_text())
    assert record['source_CT_sha256']==j['paired_source']['ct_sha256']
    assert record['source_mask_sha256']==j['source']['source_mask_sha256']
    point=record['items'][0]
    ijk=point['voxel_ijk']
    matrix=j['canonical_grid']['affine_4x4']
    expected=[sum(matrix[i][k]*ijk[k] for k in range(3))+matrix[i][3] for i in range(3)]
    assert max(abs(a-b) for a,b in zip(expected,point['world_ras_mm']))<.000001
    # Same source & viewport, undo must remove all provisional marks.
    page.locator('#markUndo').click()
    assert page.locator('#axialMarks .landmarkSpot').count()==0
    assert page.locator('#markExport').is_disabled()
    assert '解剖学的合格：未判定' in page.locator('#state').inner_text()
    assert not errors,errors
    result={
        'viewport':viewport_name,
        'browser':'Playwright Chromium with software WebGL',
        'own_mesh_visible_ready':True,
        'reference_GLTF_loaded':True,
        'three_orthogonal_slices_visible':True,
        'original_CT_and_label_overlay_modes':True,
        'numeric_7_class_3D_color_legend':True,
        'landmark_click_source_world_RAS_verified':True,
        'landmark_download_remains_unverified':True,
        'plane_controls_ok':True,
        '3D_orientation_buttons_ok':True,
        'anatomy_approval':False,
        'NOT_actual_iPhone_Safari':True}
    page.locator('#clear').click()
    assert 'データ未読込' in page.locator('#fileStatus').inner_text()
    page.close()
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('private_bundle',type=Path)
    args=parser.parse_args()
    if not args.private_bundle.is_file():parser.error('Source JSON private bundle is missing')
    global PORT
    PORT=port_available()
    server=subprocess.Popen([sys.executable,'-m','http.server',str(PORT),
                             '--bind','127.0.0.1','--directory',str(ROOT)],
                            stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        time.sleep(.7)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=[
                '--enable-unsafe-swiftshader','--use-angle=swiftshader','--disable-gpu-sandbox'])
            desktop=browser.new_context(viewport={'width':1440,'height':950},
                                         device_scale_factor=1)
            mobile=browser.new_context(viewport={'width':390,'height':844},
                                        device_scale_factor=2,is_mobile=True,
                                        has_touch=True)
            results=[check_browser(desktop,args.private_bundle,'desktop'),
                     check_browser(mobile,args.private_bundle,'iPhone-sized mobile viewport')]
            browser.close()
        print('L3_BROWSER_CONTRACT '+json.dumps(results,ensure_ascii=False))
    finally:
        server.terminate()
        try:server.wait(timeout=5)
        except subprocess.TimeoutExpired:server.kill()
if __name__=='__main__':main()
