# Keyling design

The look Keyling's projects share, written down as design tokens, so the dongle and the hub app
look like one product without copying values between them.

- `tokens/candy.json`: Candy, the dongle's default theme: palette, the app colors, corner radii and
  fonts.
- `tokens/candy-light.json`: Candy for light backgrounds, for the hub in the phone's light mode:
  the same color names as `candy.json`, without the dongle-only tokens.
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

## Rules

- A theme is one tokens file. Other themes, and later themes the dongle loads from files, use the
  same token names.
- Radii (`radius.*`, `tile-radius-ratio`) and the app colors are for the dongle's 160x80 screen; the
  hub keeps its platform's own shapes.
- Text and icons on accent, good, bad and warn use `on-accent`. Light variants meet WCAG contrast:
  4.5:1 for text colors, 3:1 for icons.
- Apps don't have colors of their own: a theme gives Settings its color and lists app colors that
  the other apps take in launcher order, so apps added later get one too.
- Tokens are renamed or removed only together with the projects that use them, since their builds
  break otherwise.

## License

MIT, see `LICENSE`. The fonts named in the tokens are not part of this repository and keep their
own licenses (SIL Open Font License 1.1).
