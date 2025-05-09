import asyncio
import os
import json
import random
import logging
from telethon import TelegramClient, events, errors
from telethon.sessions import StringSession
from telethon.errors import UserDeactivatedBanError, FloodWaitError, PhoneCodeInvalidError, SessionPasswordNeededError
from telethon.tl.functions.messages import GetHistoryRequest
from colorama import init, Fore
import pyfiglet

# Initialize colorama for colored output
init(autoreset=True)

# Define session folder
CREDENTIALS_FOLDER = 'sessions'
os.makedirs(CREDENTIALS_FOLDER, exist_ok=True)

# Set up logging
logging.basicConfig(
    filename='og_flame_service.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Auto-Reply Message
AUTO_REPLY_MESSAGE = """
Free 🆓 

https://t.me/+ZYlIT3XO1vRiM2Vl



If you want premium vip 🗿

Starts from 199 Rs ✅

SELLER = @MR_XSHOP
"""

def display_banner():
    """Display the banner using pyfiglet."""
    print(Fore.RED + pyfiglet.figlet_format("Og_Flame"))
    print(Fore.GREEN + "Made by @Og_Flame\n")

def save_credentials(session_name, credentials):
    """Save session credentials to file."""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    with open(path, "w") as f:
        json.dump(credentials, f)

def load_credentials(session_name):
    """Load session credentials from file."""
    path = os.path.join(CREDENTIALS_FOLDER, f"{session_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

async def login_to_session(session_num):
    """Handle the login process for a session with retry mechanisms."""
    session_name = f"session{session_num}"
    credentials = load_credentials(session_name)
    
    # Get credentials if not saved
    if not credentials:
        print(Fore.YELLOW + f"\nEnter details for account {session_num}:")
        credentials = {
            "api_id": input(Fore.CYAN + f"Enter API ID for session {session_num}: "),
            "api_hash": input(Fore.CYAN + f"Enter API hash for session {session_num}: "),
            "phone_number": input(Fore.CYAN + f"Enter phone number for session {session_num} (with country code): ")
        }
    
    client = TelegramClient(
        os.path.join(CREDENTIALS_FOLDER, session_name),
        int(credentials["api_id"]),
        credentials["api_hash"]
    )
    
    await client.connect()
    
    if not await client.is_user_authorized():
        print(Fore.YELLOW + f"\nLogging in to session {session_num}...")
        max_attempts = 3
        attempts = 0
        
        while attempts < max_attempts:
            try:
                await client.send_code_request(credentials["phone_number"])
                code = input(Fore.CYAN + "Enter the OTP code you received: ")
                
                try:
                    await client.sign_in(
                        phone=credentials["phone_number"],
                        code=code
                    )
                    break
                except SessionPasswordNeededError:
                    password = input(Fore.CYAN + "Enter your 2FA password: ")
                    await client.sign_in(password=password)
                    break
                    
            except PhoneCodeInvalidError:
                attempts += 1
                if attempts < max_attempts:
                    print(Fore.RED + f"Invalid code. {max_attempts - attempts} attempts remaining.")
                else:
                    print(Fore.RED + "Maximum attempts reached. Skipping this session.")
                    return None
            
            except Exception as e:
                print(Fore.RED + f"Error during login: {str(e)}")
                return None
        
        # Save credentials after successful login
        save_credentials(session_name, credentials)
    
    return client

async def get_last_saved_message(client):
    """Retrieve the last message from 'Saved Messages'."""
    try:
        saved_messages_peer = await client.get_input_entity('me')
        history = await client(GetHistoryRequest(
            peer=saved_messages_peer,
            limit=1,
            offset_id=0,
            offset_date=None,
            add_offset=0,
            max_id=0,
            min_id=0,
            hash=0
        ))
        return history.messages[0] if history.messages else None
    except Exception as e:
        logging.error(f"Failed to retrieve saved messages: {str(e)}")
        return None

async def forward_messages_to_groups(client, last_message, session_name):
    """Forward the last saved message to all groups with random delays."""
    try:
        dialogs = await client.get_dialogs()
        group_dialogs = [dialog for dialog in dialogs if dialog.is_group]

        if not group_dialogs:
            print(Fore.YELLOW + f"[{session_name}] No groups found")
            return

        print(Fore.CYAN + f"[{session_name}] Found {len(group_dialogs)} groups")

        for dialog in group_dialogs:
            group = dialog.entity
            try:
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"[{session_name}] Forwarded to {group.title}")
                logging.info(f"[{session_name}] Forwarded to {group.title}")
            except FloodWaitError as e:
                print(Fore.RED + f"[{session_name}] Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                await client.forward_messages(group, last_message)
                print(Fore.GREEN + f"[{session_name}] Forwarded after wait to {group.title}")
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Failed to forward to {group.title}: {str(e)}")
                logging.error(f"[{session_name}] Failed to forward to {group.title}: {str(e)}")

            # Random delay between 15-30 seconds
            delay = random.randint(15, 30)
            print(Fore.CYAN + f"[{session_name}] Waiting {delay} seconds before next group...")
            await asyncio.sleep(delay)

    except Exception as e:
        print(Fore.RED + f"[{session_name}] Forwarding error: {str(e)}")
        logging.error(f"[{session_name}] Forwarding error: {str(e)}")

async def setup_auto_reply(client, session_name):
    """Set up auto-reply to private messages."""
    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        if event.is_private:
            try:
                await event.reply(AUTO_REPLY_MESSAGE)
                print(Fore.GREEN + f"[{session_name}] Replied to {event.sender_id}")
                logging.info(f"[{session_name}] Replied to {event.sender_id}")
            except FloodWaitError as e:
                print(Fore.RED + f"[{session_name}] Flood wait: {e.seconds} seconds")
                await asyncio.sleep(e.seconds)
                await event.reply(AUTO_REPLY_MESSAGE)
            except Exception as e:
                print(Fore.RED + f"[{session_name}] Failed to reply: {str(e)}")
                logging.error(f"[{session_name}] Failed to reply: {str(e)}")

async def run_session(session_num, client):
    """Run both forwarding and auto-reply for a session."""
    session_name = f"session{session_num}"
    try:
        print(Fore.GREEN + f"[{session_name}] Successfully logged in")
        
        # Start auto-reply
        await setup_auto_reply(client, session_name)
        
        # Continuous forwarding with 15 minute intervals
        while True:
            last_message = await get_last_saved_message(client)
            if last_message:
                await forward_messages_to_groups(client, last_message, session_name)
            else:
                print(Fore.RED + f"[{session_name}] No saved message found")
            
            print(Fore.YELLOW + f"[{session_name}] Waiting 15 minutes before next round...")
            await asyncio.sleep(900)  # 15 minutes
            
    except UserDeactivatedBanError:
        print(Fore.RED + f"[{session_name}] Account banned")
    except Exception as e:
        print(Fore.RED + f"[{session_name}] Error: {str(e)}")
    finally:
        await client.disconnect()

async def main():
    """Main function to handle user input and execute the script."""
    display_banner()

    try:
        num_sessions = int(input(Fore.MAGENTA + "How many sessions would you like to log in? "))
        clients = []

        for i in range(1, num_sessions + 1):
            print(Fore.YELLOW + f"\n=== Processing Session {i}/{num_sessions} ===")
            client = await login_to_session(i)
            if client:
                clients.append((i, client))
                print(Fore.GREEN + f"Successfully logged in to session {i}")
            else:
                print(Fore.RED + f"Failed to log in to session {i}")

        print(Fore.GREEN + f"\nSuccessfully logged in to {len(clients)}/{num_sessions} sessions")
        
        # Run all sessions
        tasks = [run_session(session_num, client) for session_num, client in clients]
        await asyncio.gather(*tasks)

    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped by user")
    except Exception as e:
        print(Fore.RED + f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\nScript stopped")
