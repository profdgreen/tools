# lt

A smarter `tree` wrapper that keeps output readable by trimming long directory listings.

<p align="center">
  <img src="demo.svg" alt="lt demo" width="700">
</p>

## The problem

`tree` is great for exploring directory structure, but directories with many files produce overwhelming output. You end up scrolling through hundreds of lines of `sample_001.csv` through `sample_040.csv` when all you needed to know was "there are 40 CSVs in here."

## What `lt` does

- Runs `tree` with sensible defaults (`-L 2 --du -h`)
- Trims the deepest level to show the first and last few items per directory, with a count of what's hidden
- If the total output is still too long (>100 lines), progressively trims all levels to fit
- Preserves colors, Unicode tree drawing, and all `tree` flags

## Install

```bash
# clone and symlink
git clone git@git.acadian-asset.com:dgreen/tools.git
ln -s "$(pwd)/tools/lt/lt" ~/.local/bin/lt
```

Or just copy the `lt` script anywhere on your `PATH`.

## Usage

```bash
# basic usage — same as tree -L 2 --du -h
lt

# specify a directory
lt /path/to/project

# show more depth
lt -L 4

# control max items shown per directory (default: 10)
lt -m 20

# show fewer items
lt -m 4

# all tree flags work as expected
lt -d          # directories only
lt -L 3 -m 6   # 3 levels deep, 6 items per branch
```

## How trimming works

When a directory at the deepest level has more entries than `-m` (default 10), `lt` shows the first 5 and last 5 with a visual break between them:

```
├── data/
│   ├── sample_001.csv
│   ├── sample_002.csv
│   ├── sample_003.csv
│   ├── sample_004.csv
│   ├── sample_005.csv
│   ·
│   ·   (30 more items)
│   ·
│   ├── sample_036.csv
│   ├── sample_037.csv
│   ├── sample_038.csv
│   ├── sample_039.csv
│   └── sample_040.csv
```

The `·` replaces `│` to visually break the branch line, and the skip indicator is dimmed in terminals that support it.

If the output still exceeds ~100 lines after trimming the deepest level, `lt` progressively trims all levels until it fits.

## Defaults

| Setting | Default | Override |
|---------|---------|----------|
| Depth | `-L 2` | `-L N` |
| Max items per branch | `10` | `-m N` |
| Max output lines | `100` | — |
| Size display | `--du -h` | pass `--du` or `-h` to change |
