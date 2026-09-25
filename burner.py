import subprocess
import tempfile
from pathlib import Path

import pythoncom
import win32com.client
from win32comext.shell import shell

CD_SECTOR_BYTES = 2352
SECTORS_PER_SECOND = 75
TRACK_GAP_SECTORS = 150
STGM_READ_SHARE_DENY_WRITE = 0x20


def list_recorders() -> list[str]:
    disc_master = win32com.client.Dispatch("IMAPI2.MsftDiscMaster2")
    return [disc_master.Item(i) for i in range(disc_master.Count)]


def _get_recorder(recorder_unique_id: str | None = None):
    recorders = list_recorders()
    if not recorders:
        raise RuntimeError("No CD/DVD recorder found. Is the USB drive connected?")
    recorder = win32com.client.Dispatch("IMAPI2.MsftDiscRecorder2")
    recorder.InitializeDiscRecorder(recorder_unique_id or recorders[0])
    return recorder


def burn_data_disc(source_dir: Path, recorder_unique_id: str | None = None, volume_name: str = "PLAYLIST") -> None:
    if not any(source_dir.iterdir()):
        raise RuntimeError(f"No files to burn in {source_dir}.")

    recorder = _get_recorder(recorder_unique_id)

    fs_image = win32com.client.Dispatch("IMAPI2FS.MsftFileSystemImage")
    fs_image.ChooseImageDefaultsForMediaType(3)
    fs_image.VolumeName = volume_name
    fs_image.Root.AddTree(str(source_dir), False)

    result_image = fs_image.CreateResultImage()

    write_engine = win32com.client.Dispatch("IMAPI2.MsftDiscFormat2Data")
    write_engine.Recorder = recorder
    write_engine.ClientName = "cd_uploader"
    write_engine.Write(result_image.ImageStream)


def _com_message(exc: pythoncom.com_error) -> str:
    hresult, message, exc_info, _ = exc.args
    detail = (exc_info[2].strip() if exc_info and exc_info[2] else None) or message
    return f"{detail} ({hex(hresult & 0xFFFFFFFF)})"


def _mp3_to_pcm_file(mp3_path: Path, pcm_path: Path) -> int:
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3_path), "-f", "s16le", "-ar", "44100", "-ac", "2", str(pcm_path)],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"ffmpeg failed on {mp3_path.name}: {exc.stderr.decode(errors='replace')[-300:]}") from exc

    size = pcm_path.stat().st_size
    padding = (-size) % CD_SECTOR_BYTES
    if padding:
        with pcm_path.open("ab") as fh:
            fh.write(b"\x00" * padding)
        size += padding
    return size


def burn_audio_cd(mp3_files: list[Path], recorder_unique_id: str | None = None, dry_run: bool = False) -> None:
    if not mp3_files:
        raise RuntimeError("No tracks to burn.")

    recorder = _get_recorder(recorder_unique_id)

    tao = win32com.client.Dispatch("IMAPI2.MsftDiscFormat2TrackAtOnce")
    tao.Recorder = recorder
    tao.ClientName = "cd_uploader"

    if not tao.IsRecorderSupported(recorder):
        raise RuntimeError("This recorder doesn't support audio CD burning.")
    if not dry_run and not tao.IsCurrentMediaSupported(recorder):
        raise RuntimeError("No usable blank disc. Insert an unused CD-R (a partly written or damaged one won't work).")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        pcm_files = []
        needed_sectors = 0
        for i, mp3_path in enumerate(mp3_files, start=1):
            print(f"  converting {i}/{len(mp3_files)}: {mp3_path.name}")
            pcm_path = tmp_dir / f"{i:03d}.pcm"
            size = _mp3_to_pcm_file(mp3_path, pcm_path)
            pcm_files.append(pcm_path)
            needed_sectors += size // CD_SECTOR_BYTES + TRACK_GAP_SECTORS

        minutes = needed_sectors / SECTORS_PER_SECOND / 60
        print(f"  audio needs {minutes:.1f} min ({needed_sectors} sectors)")

        if dry_run:
            print("  dry run, disc untouched")
            return

        tao.PrepareMedia()
        try:
            capacity = tao.TotalSectorsOnMedia
            if needed_sectors > capacity:
                over = (needed_sectors - capacity) / SECTORS_PER_SECOND / 60
                raise RuntimeError(
                    f"Too long for this disc by {over:.1f} min "
                    f"(need {minutes:.1f} min, disc holds {capacity / SECTORS_PER_SECOND / 60:.1f} min). "
                    f"Trim tracks with --trim and retry. Disc not written, still usable."
                )

            tao.SetWriteSpeed(min(tao.SupportedWriteSpeeds), False)

            print("  writing disc, do not eject")
            for i, pcm_path in enumerate(pcm_files, start=1):
                print(f"  track {i}/{len(pcm_files)}")
                stream = shell.SHCreateStreamOnFileEx(str(pcm_path), STGM_READ_SHARE_DENY_WRITE, 0, False, None)
                tao.AddAudioTrack(stream)
        except pythoncom.com_error as exc:
            raise RuntimeError(f"Burn failed: {_com_message(exc)}") from exc
        finally:
            print("  finalizing")
            tao.ReleaseMedia()
