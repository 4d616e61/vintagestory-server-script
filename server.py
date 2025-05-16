import subprocess
import asyncio
from cfg import *
import sys
import signal
import aioconsole

G_proc : asyncio.subprocess.Process = None
G_server_ready = False


#15.5.2025 18:28:33 [Server Event] Dedicated Server now running on Port 42420 and all ips!
SERVER_START_MSG = "Dedicated Server now running"

#https://stackoverflow.com/questions/64303607/python-asyncio-how-to-read-stdin-and-write-to-stdout
async def connect_stdin_stdout():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    # w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
    # writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, None


def check_ready_line(line):
    global G_server_ready
    if SERVER_START_MSG in line:
        print("server is ready!")
        G_server_ready = True
        

def log_line(line):
    #line_txt = line.decode().rstrip("\n")
    line_txt = line
    print(f"[SERVER]{line_txt}")

#https://stackoverflow.com/questions/65649412/getting-live-output-from-asyncio-subprocess
async def _read_stream(stream, cb):  
    while True:
        try:
            line = await stream.readline()
            line = line.decode()
        except:
            break
        if line:
            for c in cb:
                c(line)
        else:
            break

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


async def setup_streams(process):
    return await asyncio.gather(
        _read_stream(process.stdout, [check_ready_line, log_line]),
        _read_stream(process.stderr, [check_ready_line, log_line])
    )


async def handle_exit():
    G_proc.terminate()
    

def setup_signal():
    loop = asyncio.get_event_loop()
    for signame in ('SIGINT', 'SIGTERM'):
        loop.add_signal_handler(getattr(signal, signame),
                                lambda: asyncio.create_task(handle_exit()))


async def send_command(proc, line):
    proc.stdin.write(line)
    await proc.stdin.drain()
    return
async def main():
    global G_proc
    setup_signal()
    proc = await init_process()
    res = setup_streams(proc)

    while True:
        line = await aioconsole.ainput()
        print("got line")
        print(line)
        #line = line.decode()
        if not line:
            break
        await send_command(G_proc, line)
       

    await res
    await handle_exit()


if __name__ == "__main__":
    asyncio.run(main())