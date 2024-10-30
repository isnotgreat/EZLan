# EZLan - Virtual LAN Gaming Network

A powerful, user-friendly application that creates virtual LAN connections over the internet, perfect for gaming and local network applications that require LAN connectivity.

**This application is made using [Cursor](https://www.cursor.dev/).**

## Features

- Easy-to-use GUI interface
- Creates a virtual network interface using Hyper-V
- Supports gaming optimizations for low latency
- Automatic port forwarding via UPnP
- Connection recovery and state management
- ...

## Prerequisites

- Windows 10 or later with Hyper-V enabled
- Administrative privileges
- Python 3.13
- `requests`
- `aiohttp`
- `qasync`
- ...

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/EZLan.git
    cd EZLan
    ```

2. **Set Up a Virtual Environment:**

    ```bash
    python -m venv venv
    ```

3. **Activate the Virtual Environment:**

    - **Windows:**

        ```bash
        venv\Scripts\activate
        ```

    - **Unix or MacOS:**

        ```bash
        source venv/bin/activate
        ```

4. **Install Dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

5. **Run the Application with Administrative Privileges:**

    ```bash
    python ezlan/main.py
    ```

## Usage

### Hosting a Network

1. Open the application.
2. Click on the **Host** button to start hosting a virtual LAN network.
3. The GUI will display the hosting status along with the assigned IP address and port.

### Connecting to a Network

1. Enter the host's public IP address and port in the **Connect** section of the GUI.
2. Click on the **Connect** button to join the virtual LAN network.

## Troubleshooting

- **No Local Area Connection Created:**
    - Ensure Hyper-V is enabled.
    - Run the application as an administrator.
    - Check the logs for any interface creation errors.

- **Port Forwarding Issues:**
    - Verify that UPnP is enabled on your router.
    - Check if the required ports are open.

- **Connection Recovery Fails:**
    - Ensure stable internet connectivity.
    - Check the logs for detailed error messages.
    - If the application shows "Unknown" as your IP, ensure your firewall allows outbound connections to `https://api.ipify.org`.

## Additional Notes

- **Enable Hyper-V:**
    - The application will attempt to enable Hyper-V if it's not already enabled.
    - If Hyper-V is enabled, you may need to restart your computer for the changes to take effect.
    - The application will prompt you if a system restart is required.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License

[MIT License](LICENSE)