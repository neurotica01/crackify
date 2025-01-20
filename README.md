# crackify

Fertilizer for your github profile

> a saturday morning test drive with aider.chat

## install

```bash
uv pip install -r requirements.txt
```

## run it

```bash
python crackify.py <repo_url> <output_dir> [options]
```

### what it does
- clones the actually impressive repo
- rewrites commits with new author info
- spreads commits with "natural" timestamps
- by default, pushes to new remote. this needs a github token to create the new repo if not exists.

### options
should just work out of the box if `git config --global user.name`, `git config --global user.email`, and `git config --global user.date` are set.

- `--name`: who you wanna be today
- `--email`: email
- `--push-url`: where to push your fake history
- `--token`: github token 

