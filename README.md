# Keyling design

The look Keyling's projects share, written down as design tokens, so the dongle and the hub app
look like one product without copying values between them.

- `tokens/candy.json`: Candy, the dongle's default theme: palette, the app colors, corner radii and
  fonts.
- `tokens/candy-light.json`: Candy for light backgrounds, for the hub in the phone's light mode:
  the same color names as `candy.json`, without radii and fonts.
- `tokens/led.json`: the status LED's colors, the same in every theme, so the hub can show the LED's
  state in the colors the dongle uses.

The files use the [Design Tokens Format](https://www.designtokens.org/) (`$value`, `$type`; colors
as sRGB hex), which tools such as Style Dictionary read.

## Using it

Projects include this repository as a git submodule and generate their constants from it:

```sh
git submodule add https://github.com/keyling-hq/design.git design
git submodule update --remote design      # pick up newer tokens, then regenerate
```

The firmware's `tools/gen_tokens.py` writes C headers from it, and its CI fails when they are out
of date.

## Logo

`logo/marks.html` is the design board: its script draws every mark, and the files next to it are
generated from it.

- `keyling-logo.svg` / `-white.svg`: the logo (mark H1g), a keycap charm on a key ring with a
  cylinder key. One filled path each, no masks or strokes, 512 px.
- `ling-happy.svg` / `-white.svg`: Ling, the keycap as a character (mark C2).
- `kp2a-plugin.svg` / `-white.svg`, `kp2a-plugin-icon.svg`: the KeePass2Android plugin's mark (P5)
  and its icon on the olive green tile.
- `github-avatar.svg` / `.png`: the organization's avatar, white on navy.

The main tile is navy `#15172B` with a white mark.

To regenerate them after changing the board, run `tools/build_icons.py`. It needs node, and Python
with `shapely` and `svgelements`. With the projects' paths it also writes their Android icons; from
this repository checked out as the android repository's `design/` submodule:

```sh
python tools/build_icons.py --hub ../hub/src/main/res \
    --plugin ../../kp2a-plugin/app/src/main/res --plugin-logo ../../kp2a-plugin/logo
```

`tools/export_marks.js` exports marks from the board as masked SVGs, and `tools/flatten.py` turns
those into single filled outlines, since Android's vector drawables have no masks. PNGs are not
generated: render them from the SVGs at the size needed.

## Rules

- A theme is one tokens file. Other themes, and later themes the dongle loads from files, use the
  same token names.
- Radii (`radius.*`, `tile-radius-ratio`) are sized for the dongle's 160x80 screen. A project that
  offers Candy's shapes as a style scales them to its own screen.
- Text and icons on accent, good, bad and warn use `on-accent`; on app colors, `on-app`. Light
  variants meet WCAG contrast: 4.5:1 for text colors, 3:1 for icons.
- The app colors are a plain list that knows nothing about apps or screens. Each project assigns
  them by position (for example Settings first, then the apps in launcher order, starting over
  after the last), so adding or removing items never changes this repository.
- Tokens are renamed or removed only together with the projects that use them, since their builds
  break otherwise.

## License

MIT, see `LICENSE`. The fonts named in the tokens are not part of this repository and keep their
own licenses (SIL Open Font License 1.1).

`logo/kp2a-plugin*.svg`: the robot head follows Keepass2Android's icon, by Philipp Crocoll. The
Android robot is reproduced or modified from work created and shared by Google and used according
to terms described in the [Creative Commons 3.0 Attribution License](https://creativecommons.org/licenses/by/3.0/).
