import subprocess
import asyncio
from cfg import *
import sys
import signal
import aioconsole
import schedule

G_proc : asyncio.subprocess.Process = None
G_server_ready = False


#15.5.2025 18:28:33 [Server Event] Dedicated Server now running on Port 42420 and all ips!
SERVER_START_MSG = "Dedicated Server now running"


async def _autosave_async():
    global G_proc
    print('talk')
    await send_command(G_proc, b"hi")
    
def autosave():
    global G_server_ready
    if not G_server_ready:
        return
    asyncio.run(_autosave_async())



schedule.every(C_AUTOSAVE_INTERVAL_MINS).seconds.do(autosave)


def check_ready_line(line):
    global G_server_ready
    if SERVER_START_MSG in line:
        print("server is ready!")
        G_server_ready = True
        

def log_line(line):
    line_txt = line.rstrip("\n")
    print(f"{line_txt}")

#https://stackoverflow.com/questions/65649412/getting-live-output-from-asyncio-subprocess
async def _read_stream(stream, cb):  
    while True:
        try:
            line = await stream.readline()
            line = line.decode()
        except:
            break
        if not line:
            break

        for c in cb:
            c(line)

async def init_process():
    global G_proc

    G_proc = await asyncio.create_subprocess_exec(
            "./vintagestory/VintagestoryServer",
            "--dataPath", 
            C_DATA_DIR,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
    )

    return G_proc

#whoever made this example i HATE you
def setup_streams(process):
    return asyncio.gather(
        _read_stream(process.stdout, [check_ready_line, log_line]),
        _read_stream(process.stderr, [check_ready_line, log_line])
    )


async def handle_exit():
    try:
        G_proc.terminate()
    except:
        pass
    

async def run_peding():
    while True:
        try:
            schedule.run_pending()
        except:
            return
        asyncio.sleep(100)

def setup_signal():
    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.create_task(handle_exit()))


async def send_command(proc, line):
    proc.stdin.write(line + b"\n")
    await proc.stdin.drain()
    return

async def main():
    global G_proc
    setup_signal()
    proc = await init_process()
    res = setup_streams(proc)
    res2 = run_peding()

    while True:
        try:
            line = await aioconsole.ainput()
            line = line.encode()
        except EOFError:
            print("eof")
            break
        if not line:
            continue
        await send_command(G_proc, line)
       

    await res
    await res2
    await handle_exit()


if __name__ == "__main__":
    asyncio.run(main())