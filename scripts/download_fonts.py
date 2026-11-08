from pathlib import Path
import urllib.request
root=Path(__file__).resolve().parent.parent/'assets/fonts'
root.mkdir(parents=True,exist_ok=True)
urls={
'NotoSans-Regular.ttf':'https://raw.githubusercontent.com/notofonts/noto-fonts/main/hinted/ttf/NotoSans/NotoSans-Regular.ttf',
'NotoSansDevanagari-Regular.ttf':'https://raw.githubusercontent.com/notofonts/noto-fonts/main/hinted/ttf/NotoSansDevanagari/NotoSansDevanagari-Regular.ttf',
'OFL.txt':'https://raw.githubusercontent.com/notofonts/noto-fonts/main/LICENSE',
}
for name,url in urls.items():
 urllib.request.urlretrieve(url,root/name)
 print('Downloaded',name)
