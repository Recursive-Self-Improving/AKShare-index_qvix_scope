import sys
import shutil
import json
from pathlib import Path
sys.path.insert(0, '/root/github.com/Recursive-Self-Improving/AKShare-index_news_sentiment_scope')
from app.chart import build
from app.core import csv_bytes
repo=Path(sys.path[0])
root=Path('/tmp/sentiment-browser-round1/fixture-data')
shutil.copytree(repo/'data',root)
m=json.loads((root/'latest.json').read_text())
dates=['2024-10-21','2024-10-22','2024-10-23','2024-10-24','2024-10-25','2024-10-28','2024-10-29','2024-10-30','2024-10-31']
for code,values in [('sh000001',[10,11,12,13,14,15,16,17,18]),('sh000016',[10,11,'omit',13,14,None,0,12,14])]:
    rows=[dict(date=d,close=v,pre_release=0,pre_base=0) for d,v in zip(dates,values) if v!='omit']
    (root/m['feeds'][code]['snapshot']['csv']).write_bytes(csv_bytes(rows,['date','close','pre_release','pre_base']))
    m['feeds'][code]['snapshot']['range']=[dates[0],dates[-1]]
m['feeds']['sh000016']['relative_gaps']=['2024-10-23']
(root/'latest.json').write_text(json.dumps(m))
build(root,'/tmp/sentiment-browser-round1/synthetic-fixture.html')
