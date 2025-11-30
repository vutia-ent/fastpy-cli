# Homebrew Tap Setup

To distribute Fastpy via Homebrew, you need to create a separate repository for the tap.

## Setup Steps

### 1. Create the tap repository

Create a new GitHub repository named `homebrew-tap` under `vutia-ent`:
- Repository: `vutia-ent/homebrew-tap`

### 2. Add the formula

Copy `fastpy.rb` to the tap repository:

```bash
git clone https://github.com/vutia-ent/homebrew-tap.git
cp fastpy.rb homebrew-tap/Formula/fastpy.rb
cd homebrew-tap
git add .
git commit -m "Add fastpy formula"
git push
```

### 3. Update SHA256 hashes

After publishing to PyPI, update the SHA256 hashes in the formula:

```bash
# Get SHA256 for the main package
curl -sL https://files.pythonhosted.org/packages/source/f/fastpy-cli/fastpy-cli-0.1.0.tar.gz | shasum -a 256

# Or use pip download
pip download fastpy-cli --no-deps -d /tmp
shasum -a 256 /tmp/fastpy-cli-0.1.0.tar.gz
```

### 4. Users can then install

```bash
brew tap vutia-ent/tap
brew install fastpy
```

Or in one command:

```bash
brew install vutia-ent/tap/fastpy
```

## Updating the Formula

When releasing a new version:

1. Update `url` with new version
2. Update `sha256` with new hash
3. Commit and push to the tap repository
