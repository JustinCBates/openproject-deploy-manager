# Dependencies for Deploy Manager

## Production Dependencies (Required for all users)

### Absolute (Always needed)
- docker                       # Container management
- docker-compose               # Container orchestration
- python>=3.8                  # Python runtime

### Ad Hoc (Needed for optional features)
- curl                         # HTTP requests (if downloading images)
- openssl                      # SSL certificates (if managing certificates)
- tar                          # Archive handling (if backup/restore)

## Developer Dependencies (Only needed for development)

### Absolute (Core development tools)
- git                          # Version control
- python>=3.8                  # Python runtime

### Ad Hoc (Optional development tools)
- pytest                       # Testing (if adding tests)
- black                        # Code formatting (if formatting code)
- shellcheck                   # Shell script validation (if using shell scripts)

## Installation Commands

### Production Only (Minimal)
```bash
# System dependencies
sudo apt-get install docker.io docker-compose python3

# Python dependencies (if any Python code added)
pip3 install -r requirements.txt
```

### Development Environment
```bash
# Development tools
sudo apt-get install git python3-pip
pip3 install pytest black
```

## Notes
- Primarily uses system tools (docker, docker-compose)
- Python dependencies added as Python code is developed
- Shell scripts should be validated with shellcheck
- Update this file when adding new dependencies
