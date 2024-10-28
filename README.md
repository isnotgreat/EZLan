# EZLan - Virtual LAN Gaming Network

A powerful, user-friendly application that creates virtual LAN connections over the internet, perfect for gaming and local network applications that require LAN connectivity.

## Features

- Easy-to-use GUI interface
- Automatic peer discovery on local networks
- Secure password-protected hosting
- Virtual network adapter configuration
- NAT traversal for internet connectivity
- Connection monitoring and status feedback
- Cross-platform support (Windows/Linux)

## Requirements

- Python 3.8 or higher
- Administrator privileges (required for network adapter configuration)
- TAP driver (automatically installed on first run)
- Internet connection for online gaming

## Installation

### Method 1: Direct Download
1. Download and extract the EZLan application
2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

### Method 2: From GitHub
1. Clone the repository:
```bash
git clone https://github.com/isnotgreat/ezlan.git
cd ezlan
```
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Hosting a Network

1. Launch EZLan with administrator privileges
2. Click "Host"
3. Enter your desired network name and password
4. Share the displayed IP and port with friends

### Joining a Network

1. Launch EZLan with administrator privileges
2. Click "Connect"
3. Choose connection method:
   - Local Network: Select from discovered peers
   - Direct Connection: Enter host's IP and port

## Troubleshooting

- **TAP Driver Issues**: If you see TAP driver errors, try restarting your computer after first installation
- **Connection Failed**: Ensure the host has properly forwarded ports and configured firewall
- **Not Responding**: Only run one instance of EZLan at a time

## Technical Details

- Uses TAP virtual network adapters for LAN emulation
- Implements NAT traversal for peer-to-peer connectivity
- Supports both IPv4 and IPv6 networks
- Automatic port forwarding configuration
- Secure authentication and encryption

## Development

The application is structured into several key components:
- Network Services (Discovery, Tunnel)
- System Configuration
- User Interface
- Connection Management

## License

MIT License - See LICENSE file for details

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request