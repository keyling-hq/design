// Exports marks from logo/marks.html as masked SVGs, by running the board's script with a stub document.
// Usage: node export_marks.js <marks.html> <out dir> <id>=<name> [<id>=<name> ...]
// Writes <name>.svg (navy) and <name>-white.svg for each mark.
const fs = require("fs");
const path = require("path");

const [src, outDir, ...pairs] = process.argv.slice(2);
if (!src || !outDir || pairs.length === 0) {
  console.error("usage: node export_marks.js <marks.html> <out dir> <id>=<name> ...");
  process.exit(2);
}
const html = fs.readFileSync(src, "utf8");
const script = html.slice(html.indexOf("<script>") + 8, html.lastIndexOf("</script>"));
const el = () => ({ style: { setProperty() {} }, set innerHTML(v) {}, querySelectorAll: () => [], addEventListener() {} });
const document = { getElementById: el, querySelectorAll: () => [], fonts: { load: async () => {} } };
const { svg, FAMILIES, CHAIN_MARKS, PLUGIN_MARKS } = new Function("document",
  script + "\nreturn { svg, FAMILIES, CHAIN_MARKS, PLUGIN_MARKS };")(document);
const all = [...FAMILIES.flatMap(fam => fam.marks), ...CHAIN_MARKS, ...PLUGIN_MARKS];

fs.mkdirSync(outDir, { recursive: true });
for (const pair of pairs) {
  const [id, name] = pair.split("=");
  const m = all.find(x => x.id === id);
  if (!m) {
    console.error(`no mark with id ${id}`);
    process.exit(1);
  }
  for (const [suffix, color] of [["", "#15172B"], ["-white", "#FFFFFF"]]) {
    let s = svg(m, { viewBox: "18 18 72 72", size: 512, xmlns: true });
    s = s.replace('style="color:#FFFFFF"', `style="color:${color}"`).replace(' class=""', "").replace(' aria-hidden="true"', "");
    const file = path.join(outDir, `${name}${suffix}.svg`);
    fs.writeFileSync(file, '<?xml version="1.0" encoding="UTF-8"?>\n' + s + "\n");
    console.log(file);
  }
}
