# crackify

make your git history look like you actually work. because apparently commit streaks matter more than actual code.

## install

```bash
uv pip install -r requirements.txt
```

## run it

```bash
python crackify.py <repo_url> <output_dir> [options]
```

### what it does
- clones your too-clean repo
- rewrites commits with new author info
- spreads commits with "natural" timestamps
- (optional) pushes to new remote

### options
- `--name`: who you wanna be today
- `--email`: your new fake email
- `--push-url`: where to push your fake history
- `--token`: github token (they don't trust you)

> warning: this won't make you better at coding. it just makes you look busy. use at your own risk.
