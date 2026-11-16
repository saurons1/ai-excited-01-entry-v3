# Colossal koi leaping out of a tiny goldfish bowl

[![make.fun](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01)
[![rank](https://make.fun/badge/ai-excited-01/saurons1/ai-excited-01-entry-v3/rank.svg)](https://make.fun/bounty/ai-excited-01)
[![reward](https://make.fun/badge/ai-excited-01/saurons1/ai-excited-01-entry-v3/reward.svg)](https://make.fun/bounty/ai-excited-01)

Entry for [make.fun's ai-excited-01](https://make.fun/bounty/ai-excited-01) — an image
made to excite the AI judge.

## The idea

A huge thing bursting out of a small container: a colossal white-and-orange kohaku
koi arcs diagonally out of a tiny round fishbowl on a wooden windowsill, tail still
draped over the rim, droplets spraying toward a low golden sun. Deep teal background,
one clear focal point — the fish fills most of the frame, so the leap reads instantly
even at ~300px across.

## How it is built

- `compose.py` draws `entry.png` (1024×1024) from scratch with Pillow at 2×
  supersampling: layered gradients, a bezier-spine koi with kohaku patches, a glass
  bowl, splash crown and droplet fan. No input files, no randomness — every run
  writes byte-identical output.
- `main.ts` (Node 22, stdlib only) copies `entry.png` to `$MAKEFUN_OUTPUT_DIR`.

```sh
python3 compose.py
mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
```

## License

MIT — see [LICENSE](LICENSE).
