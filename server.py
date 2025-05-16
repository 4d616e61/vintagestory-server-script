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

async def send_command(proc, line):
    proc.stdin.write(line + b"\n")
    await proc.stdin.drain()
    return


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
        print("Failed to kill subprocess. Manual intervention may be required.")
        print(f"kill {G_proc.pid}")
        pass
    



def setup_signal():
    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.create_task(handle_exit()))

async def run_peding_loop():
    while True:
        try:
            schedule.run_pending()
            await asyncio.sleep(0.1)
        except:
            return

async def forward_input_loop():
    while True:
        try:
            line = await aioconsole.ainput()
            line = line.encode()
        except EOFError:
            break
        if not line:
            continue
        await send_command(G_proc, line)



async def _autosave_async():
    global G_proc
    print('talk')
    await send_command(G_proc, b"hi")
    
def autosave():
    global G_server_ready
    if not G_server_ready:
        return
    event_loop = asyncio.get_event_loop()
    asyncio.ensure_future(_autosave_async(), loop=event_loop)
    


schedule.every(1).seconds.do(autosave)


async def main():
    global G_proc
    global G_server_ready
    setup_signal()
    proc = await init_process()
    res = setup_streams(proc)
    res2 = asyncio.create_task(run_peding_loop())
    res3 = asyncio.create_task(forward_input_loop())
    
       

    await res

    res2.cancel()
    res3.cancel()
    await handle_exit()


if __name__ == "__main__":
    asyncio.run(main())