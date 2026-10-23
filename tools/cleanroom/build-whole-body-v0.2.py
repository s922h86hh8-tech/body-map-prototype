from pathlib import Path
import json
root=Path(__file__).resolve().parents[2]
s=(root/'experiments/cleanroom-whole-body-v0.1.html').read_text()
s=s.replace('全身骨格 0.1','全身骨格 0.2').replace('独自全身骨格 0.1','独自全身骨格 0.2')
s=s.replace('<summary>形状と制作状況</summary>','<summary>形状と制作状況</summary><p>v0.2では肩・骨盤・膝の高さと腕脚の配分を、成人の人体寸法統計を参考に調整しました。骨の関節中心を実測したモデルではありません。</p><p>比率の参考：<a href="https://www.airc.aist.go.jp/dhrt/fbodydb/index.html">産業技術総合研究所 AIST/HQL人体寸法・形状データベース2003</a>（青年男性群の公開集計値）。頭部・足部・骨面の詳細寸法は独自の模式設計です。</p>')
s=s.replace('<footer>','<footer><a href="cleanroom-whole-body-v0.1.html">旧版0.1と比較</a> · ')
start=s.index('function build(){');end=s.index('build();',start)
params={'version':'0.2','morphology_source':'Gray 1918 original descriptions; skull, cervical/thoracic/lumbar spine, scapula, hip bone; source list in handoff','units':'arbitrary drawing units','height':177,'source':'https://www.airc.aist.go.jp/dhrt/fbodydb/2003_Statistics.pdf','cohort':'young adult male, N=49; ratio of aggregate means, not population mean of individual ratios','means_mm':{'height':1696.7,'acromiale':1363.5,'iliocristale':957.2,'trochanterion_laterale':832.0,'mid_patella':448.9,'upper_arm':315.5,'forearm':250.8},'design':{'cranial_center':[0,-1.7,168],'cranial_radii':[7.5,9.2,9],'ankle_z':7,'hip_head_above_trochanter':3,'foot_y_scale':1.3},'limitations':'Surface anthropometry guides vertical layout only. Bone centers, widths, head and foot dimensions are original schematic design; no skeletal measurement or individual scan.'}
code='const PROPORTIONS='+json.dumps(params,ensure_ascii=False,separators=(',',':'))+';\n'
code+='''const BODY_H=PROPORTIONS.height, M=PROPORTIONS.means_mm;
const A={shoulder:BODY_H*M.acromiale/M.height,crest:BODY_H*M.iliocristale/M.height,trochanter:BODY_H*M.trochanterion_laterale/M.height,knee:BODY_H*M.mid_patella/M.height};
A.radial=A.shoulder-BODY_H*M.upper_arm/M.height;A.wrist=A.radial-BODY_H*M.forearm/M.height;
function build(){
ell('頭蓋','head','M',[0,0,166],[9.2,8.5,11]);tube('下顎','head','M',[[-6.5,3,158],[-5.6,7.5,155],[0,9,154.5],[5.6,7.5,155],[6.5,3,158]],1.2);
for(let i=0;i<24;i++){let z=i<7?157-i*1.2:i<19?147.2-(i-7)*2.4:117.7-(i-19)*3.1,reg=i<7?'neck':i<19?'back':'lumbar',w=i<7?2.5:i<19?3.2:4;ell('椎体'+(i+1),reg,'M',[0,-1.5+Math.sin(i*.23)*1.5,z],[w,2.6,i<7?.52:1.15]);tube('椎弓模式'+(i+1),reg,'M',[[-w,-1,z],[0,-6,z],[w,-1,z]],i<7?.45:.7)}
ell('仙骨','pelvis','M',[0,-2,96],[5,3,7]);tube('尾骨','pelvis','M',[[0,-2,90],[0,0,86]],1);
bone('胸骨','chest','M',[0,10,A.shoulder-1],[0,12,122],1.8);
for(const s of [-1,1]){let side=s>0?'R':'L',p=(x,y,z)=>[s*x,y,z];
for(let i=0;i<12;i++){let z=145.5-i*2.4,w=9+8*Math.sin((i+2)/15*Math.PI),pts=[];for(let j=0;j<=16;j++){let a=j*Math.PI*(i<7?1:.85)/16;pts.push(p(1.5+w*Math.sin(a),-3+7.5*(1-Math.cos(a)),z-4*Math.sin(a/2)))}tube('肋骨'+(i+1),'chest',side,pts,.65)}
tube('鎖骨','shoulder',side,[p(1,9,A.shoulder),p(8,10,A.shoulder+1),p(16,6,A.shoulder+.5),p(21,3,A.shoulder)],1.25);
add('肩甲骨模式','shoulder',side,[p(5,-7,A.shoulder),p(20,-5,A.shoulder),p(10,-8,A.shoulder-18),p(11,-9,A.shoulder-4)],[[0,1,2],[0,3,1],[1,3,2],[2,3,0]]);
let crest=A.crest-2.4,hip=A.trochanter+3;
tube('寛骨模式','pelvis',side,[p(4,-3,crest-2),p(12,-4,crest),p(18,-1,crest-4),p(15,3,hip),p(9,4,hip-7),p(3,6,hip-10),p(8,-1,hip-13),p(13,-4,hip-9),p(15,3,hip)],2.4);
bone('上腕骨','arm',side,p(22,1,A.shoulder-2.5),p(27,1,A.radial+1.2),2);
bone('橈骨','forearm',side,p(29,2,A.radial),p(33,3,A.wrist),1.15);bone('尺骨','forearm',side,p(26,0,A.radial+1.5),p(29,2,A.wrist),1.05);
let wrist=A.wrist;
ell('手根部一括','hand',side,p(31,3,wrist-2.5),[3,1.6,2]);
for(let d=0;d<5;d++){let x=27.5+d*1.65,z=wrist-5.5-(d===0?1:0),end=wrist-11.5+Math.abs(d-2)*.8;bone('中手骨'+(d+1),'hand',side,p(x,3,z),p(x+(d===0?-3:0),3,end),.55);let n=d===0?2:3;for(let k=0;k<n;k++)bone('指節'+(d+1)+'-'+(k+1),'hand',side,p(x+(d===0?-3:0),3,end-k*2.5),p(x+(d===0?-3:0),3,end-(k+1)*2.5+.3),.5)}
ell('大腿骨頭','thigh',side,p(8,1,hip),[3.2,3.2,3.2]);bone('大腿骨頸部','thigh',side,p(8,1,hip),p(14,0,A.trochanter),2.1);bone('大腿骨体','thigh',side,p(14,0,A.trochanter),p(11,0,A.knee+1),2.4);ell('膝蓋骨','thigh',side,p(11,3.5,A.knee),[2.1,1.2,2.4]);
bone('脛骨','leg',side,p(11,0,A.knee-3),p(10,0,7),1.9);bone('腓骨','leg',side,p(15,-.6,A.knee-3.5),p(13,-.6,6),.85);
ell('足根部一括','foot',side,p(11,2,2.3),[3.2,5.8,2.3]);for(let d=0;d<5;d++){let x=8.5+d*1.4,end=15.6-Math.abs(d-1)*.65;bone('中足骨'+(d+1),'foot',side,p(x,6.5,1.5),p(x,end,1.5),.6);let n=d===0?2:3;for(let k=0;k<n;k++)bone('趾節'+(d+1)+'-'+(k+1),'foot',side,p(x,end+k*2.08,1.5),p(x,end+(k+1)*2.08-.2,1.5),.48)}
}}
'''
s=s[:start]+code+s[end:]
# Add shape detail to the same unpublished revision.
helper=(root/'tools/cleanroom/whole-body-morphology-v0.2.js').read_text()
s=s.replace('function build(){',helper+'\nfunction build(){',1)
a=s.index("ell('頭蓋','head','M'"); b=s.index("bone('胸骨'",a)
s=s[:a]+"skull();spine();sacrum();\n"+s[b:]
a=s.index("add('肩甲骨模式'");b=s.index("bone('上腕骨'",a)
s=s[:a]+"scapula(s);pelvisSide(s);let hip=A.trochanter+3;\n"+s[b:]
s=s.replace("bone('上腕骨','arm',side,p(22,1,A.shoulder-2.5),p(27,1,A.radial+1.2),2);", "shaft('上腕骨体','arm',side,p(22,1,A.shoulder-3.5),p(27,1,A.radial+2),1.7,1.45);ell('上腕骨頭','arm',side,p(21,0,A.shoulder-2.8),[2.7,2.5,2.7]);ell('上腕骨遠位端','arm',side,p(27,1,A.radial+1),[3,1.8,1.7]);")
s=s.replace("bone('大腿骨体','thigh',side,p(14,0,A.trochanter),p(11,0,A.knee+1),2.4);", "shaft('大腿骨体','thigh',side,p(14,0,A.trochanter),p(11,0,A.knee+1),2.3,2);ell('大転子模式','thigh',side,p(14,-.3,A.trochanter+1),[2.1,2.2,3.5]);for(let q of [-1,1])ell('大腿骨顆','thigh',side,p(11+q*1.7,-.4,A.knee+1),[1.8,2.5,2.6]);")
s=s.replace("bone('脛骨','leg',side,p(11,0,A.knee-3),p(10,0,7),1.9);", "shaft('脛骨体','leg',side,p(11,0,A.knee-3),p(10,0,7),2,1.3);ell('脛骨近位端','leg',side,p(11,0,A.knee-3),[3.2,2.3,1.5]);ell('内果模式','leg',side,p(9,0,6.5),[1.2,1.4,2]);")
s=s.replace('頭蓋と下顎の概形。','眼窩・鼻部・頬骨弓・上下顎と歯列を追加。').replace('歯・縫合・孔・顔面骨の分離は未制作。','骨の縫合・鼻腔内部・細かな孔と関節面は未制作。骨面の監査は未完了。')
s=s.replace('頸椎7個の位置を模式表示。','環椎・軸椎と典型頸椎の形を分け、椎孔・突起を追加。').replace('各椎骨の突起・環椎・軸椎の固有形状は未制作。','個々の関節面と横突孔・椎孔の寸法や形状精度は未承認。')
s=s.replace('胸椎12個を中心とする背部。','胸椎12個に椎体・椎弓・横突起・後下方へ向く棘突起を追加。').replace('腰椎5個の位置。','腰椎5個に幅の広い椎体・椎弓・棘突起・横突起を追加。')
s=s.replace('寛骨は輪郭状の模式形状。孔・関節面・筋付着は未承認。','腸骨翼・恥骨枝・坐骨枝・仙骨孔を追加。関節面・筋付着は未承認。')
s=s.replace('肩甲骨の面・関節窩は簡略形状。','肩甲骨体・肩甲棘・肩峰・烏口突起を追加。関節面は簡略形状。')
s=s.replace('頭蓋の孔・縫合、椎骨の突起、骨の関節面、手根骨・足根骨の個別形状などは未制作です。','頭蓋・椎骨・肩甲骨・骨盤の形を追加していますが、縫合・細かな関節面、手根骨・足根骨の個別形状などは未制作です。')
s=s.replace('頭部・足部・骨面の詳細寸法は独自の模式設計です。','頭部・足部・骨面の詳細寸法は独自の模式設計です。頭蓋と椎骨などの構造はGray 1918の原著記述と照合し、画像輪郭・頂点を取り込まず造形しました。')
s=s.replace('ctx.closePath();ctx.fill()','ctx.closePath();ctx.fill();if(f.seam){ctx.strokeStyle=ctx.fillStyle;ctx.lineWidth=.35;ctx.stroke()}')
# Give orbit/nasal recesses a simple cavity-occlusion term using actual 3D coordinates.
s=s.replace('faces.push({ps,z:ps.reduce((s,p)=>s+p[2],0)/3,lit,selected})', "let occlusion=1;if(o.name==='頭蓋・眼窩・梨状口'){let c=f.map(i=>o.verts[i]).reduce((a,p)=>a.map((v,i)=>v+p[i]/3),[0,0,0]);let eye=Math.min(ed(c,[3.45,8.9,163.6],[2.3,4.2,2.25]),ed(c,[-3.45,8.9,163.6],[2.3,4.2,2.25])),nose=ed(c,[0,9,159.9],[1.15+.25*Math.max(0,160.8-c[2]),3.6,2.15]);if(c[1]<9&&(Math.abs(eye)<.22||Math.abs(nose)<.22))occlusion=.5+.4*Math.max(0,(c[1]-5)/4)}faces.push({ps,z:ps.reduce((s,p)=>s+p[2],0)/3,lit:lit*occlusion,selected,seam:o.name==='頭蓋・眼窩・梨状口'})")

s=s.replace('<button data-view="left">左側</button>','<button data-view="left">左側</button><button data-view="oblique">斜め</button><button data-view="top">上から</button>')
s=s.replace("right:Math.PI/2,left:-Math.PI/2}[v];state.pitch=0", "right:Math.PI/2,left:-Math.PI/2,oblique:-.55,top:0}[v];state.pitch=v==='top'?1.25:v==='oblique'?.15:0")
s=s.replace("right:'右から',left:'左から'}[v]", "right:'右から',left:'左から',oblique:'斜めから',top:'上から'}[v]")

(root/'experiments/cleanroom-whole-body-v0.2.html').write_text(s)
(root/'assets/cleanroom/whole-body-proportions.v0.2.json').write_text(json.dumps(params,ensure_ascii=False,indent=2)+'\n')
