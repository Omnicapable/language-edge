from pathlib import Path

root = Path(__file__).resolve().parents[1]
css = root / 'language_edge/web/style.css'
text = css.read_text(encoding='utf-8')
palette = {
    '#101512':'#090909', '#171d19':'#171717', '#303a32':'#353535',
    '#a3b0a6':'#ababab', '#eef1e8':'#f2f2f2', '#d9e8b0':'#f5f5f5',
    '#69baf4':'#eeeeee', '#111813':'#111111', '#17200e':'#111111',
    '#778671':'#888888', '#7b8b80':'#929292', '#ffb4a3':'#ffffff',
    '#1c2a24':'#222222', '#6e9983':'#999999', '#b798ec':'#777777',
    '#ffb073':'#ffffff', '#141b16':'#131313', '#0b110d':'#080808',
    '#111d17':'#191919', '--blue':'--mesh',
}
for before, after in palette.items():
    text = text.replace(before, after)
text += '\n/* Shape, as well as tone, distinguishes groups without color. */\n.legend i{width:7px;height:7px;flex-shrink:0}.legend .reference{background:#f5f5f5}.legend .calibration{border-radius:0;background:#aaa}.legend .evaluation{border-radius:0;background:#888;clip-path:polygon(50% 0,100% 100%,0 100%)}.legend .query{border-radius:0;background:transparent;border:1px solid #fff;transform:rotate(45deg)}#error:not(:empty){border-left:2px solid #fff;padding-left:10px}\n'
css.write_text(text,encoding='utf-8')
html = root / 'language_edge/web/index.html'
text = html.read_text(encoding='utf-8')
text = text.replace('Blue envelope','Coverage envelope').replace('The blue mesh','The wireframe mesh').replace('The blue surface','The wireframe surface')
html.write_text(text,encoding='utf-8')
