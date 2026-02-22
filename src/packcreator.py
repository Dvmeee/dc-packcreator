"""Pack creator with Tkinter GUI and reusable create_pack function."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zipfile


REQUIRED_PACK_FOLDERS = ("audioconfig", "data", "stream", "sfx")
DEFAULT_TEMPLATE_DIR = "xyz"
META_EXTENSIONS = {".meta"}
STREAM_EXTENSIONS = {
	".yft",
	".ytd",
	".ycd",
	".ydr"
}


def _write_template_files(archive: zipfile.ZipFile, audioconfig_path: str, sfx_path: str, fxmanifest_path: str) -> None:
	audio_path = Path(audioconfig_path).expanduser().resolve()
	if not audio_path.is_dir():
		raise NotADirectoryError(f"audioconfig is not a directory: {audio_path}")

	sfx_resolved = Path(sfx_path).expanduser().resolve()
	if not sfx_resolved.is_dir():
		raise NotADirectoryError(f"sfx is not a directory: {sfx_resolved}")

	manifest = Path(fxmanifest_path).expanduser().resolve()
	if not manifest.is_file():
		raise FileNotFoundError(f"fxmanifest.lua not found: {manifest}")

	archive.write(manifest, "fxmanifest.lua")

	for root, _, files in os.walk(audio_path):
		root_path = Path(root).resolve()
		relative_root = root_path.relative_to(audio_path)
		if not files and relative_root != Path("."):
			archive.writestr((Path("audioconfig") / relative_root).as_posix() + "/", "")

		for file_name in files:
			file_path = root_path / file_name
			target = Path("audioconfig") / relative_root / file_name
			archive.write(file_path, target.as_posix())

	for root, _, files in os.walk(sfx_resolved):
		root_path = Path(root).resolve()
		relative_root = root_path.relative_to(sfx_resolved)
		if not files and relative_root != Path("."):
			archive.writestr((Path("sfx") / relative_root).as_posix() + "/", "")

		for file_name in files:
			file_path = root_path / file_name
			target = Path("sfx") / relative_root / file_name
			archive.write(file_path, target.as_posix())


def create_pack(source_folder: str, output_folder: str = "output", pack_name: str | None = None) -> str:
	source_path = Path(source_folder).expanduser().resolve()

	if not source_path.exists():
		raise FileNotFoundError(f"Source folder not found: {source_path}")
	if not source_path.is_dir():
		raise NotADirectoryError(f"Source path is not a directory: {source_path}")

	output_path = Path(output_folder).expanduser().resolve()
	output_path.mkdir(parents=True, exist_ok=True)

	if pack_name:
		zip_name = f"{pack_name}.zip"
	else:
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		zip_name = f"pack_{timestamp}.zip"

	zip_path = output_path / zip_name

	with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for folder_name in REQUIRED_PACK_FOLDERS:
			archive.writestr(f"{folder_name}/", "")

		for root, dirs, files in os.walk(source_path):
			current_root = Path(root).resolve()

			dirs[:] = [
				directory
				for directory in dirs
				if (current_root / directory).resolve() != output_path
			]

			for file_name in files:
				file_path = current_root / file_name
				if file_path.resolve() == zip_path:
					continue

				relative_path = file_path.relative_to(source_path)
				archive.write(file_path, relative_path.as_posix())

	return str(zip_path)


def create_carpack(
	vehicle_folders: list[str],
	output_folder: str = "output",
	pack_name: str | None = None,
	template_dir: str | None = None,
	audioconfig_path: str | None = None,
	sfx_path: str | None = None,
	fxmanifest_path: str | None = None,
) -> str:
	if not vehicle_folders:
		raise ValueError("At least one vehicle folder must be provided.")

	resolved_vehicle_folders: list[Path] = []
	for folder in vehicle_folders:
		vehicle_path = Path(folder).expanduser().resolve()
		if not vehicle_path.exists():
			raise FileNotFoundError(f"Vehicle folder not found: {vehicle_path}")
		if not vehicle_path.is_dir():
			raise NotADirectoryError(f"Vehicle path is not a directory: {vehicle_path}")
		resolved_vehicle_folders.append(vehicle_path)

	output_path = Path(output_folder).expanduser().resolve()
	output_path.mkdir(parents=True, exist_ok=True)

	if pack_name:
		zip_name = f"{pack_name}.zip"
	else:
		timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
		zip_name = f"carpack_{timestamp}.zip"

	zip_path = output_path / zip_name

	if not audioconfig_path or not sfx_path or not fxmanifest_path:
		if not template_dir:
			raise ValueError("Either individual template paths or template_dir must be provided.")
		template_path = Path(template_dir).expanduser().resolve()
		audioconfig_path = str(template_path / "audioconfig")
		sfx_path = str(template_path / "sfx")
		fxmanifest_path = str(template_path / "fxmanifest.lua")

	with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for folder_name in REQUIRED_PACK_FOLDERS:
			archive.writestr(f"{folder_name}/", "")

		_write_template_files(archive, audioconfig_path, sfx_path, fxmanifest_path)

		for vehicle_root in resolved_vehicle_folders:
			vehicle_name = vehicle_root.name
			for root, _, files in os.walk(vehicle_root):
				current_root = Path(root).resolve()
				for file_name in files:
					if file_name == "fxmanifest.lua":
						continue

					file_path = current_root / file_name
					if file_path.resolve() == zip_path:
						continue

					extension = file_path.suffix.lower()
					relative_file = file_path.relative_to(vehicle_root)

					target_path = None

					if relative_file.parts and relative_file.parts[0] == "data":
						inner_relative = Path(*relative_file.parts[1:])
						inner_ext = inner_relative.suffix.lower()
						if inner_ext in META_EXTENSIONS or inner_ext in STREAM_EXTENSIONS:
							target_path = Path("data") / vehicle_name / inner_relative
					elif relative_file.parts and relative_file.parts[0] == "stream":
						inner_relative = Path(*relative_file.parts[1:])
						inner_ext = inner_relative.suffix.lower()
						if inner_ext in STREAM_EXTENSIONS:
							target_path = Path("stream") / vehicle_name / inner_relative
					else:
						if extension in META_EXTENSIONS:
							target_path = Path("data") / vehicle_name / relative_file
						elif extension in STREAM_EXTENSIONS:
							target_path = Path("stream") / vehicle_name / relative_file

					if target_path:
						archive.write(file_path, target_path.as_posix())

	return str(zip_path)


class PackCreatorApp:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Pack Creator")
		self.root.geometry("700x500")
		self.selected_folders: list[str] = []
		self.output_folder: str | None = None
		self.audioconfig_path: str | None = None
		self.sfx_path: str | None = None
		self.fxmanifest_path: str | None = None
		self.name_entry: ttk.Entry | None = None

		self._setup_style()
		self._build_ui()

	def _setup_style(self) -> None:
		style = ttk.Style(self.root)
		style.theme_use("clam")

		style.configure("Card.TFrame", background="#ffffff")
		style.configure("Title.TLabel", background="#ffffff", foreground="#111827", font=("Helvetica", 18, "bold"))
		style.configure("Text.TLabel", background="#ffffff", foreground="#4b5563", font=("Helvetica", 11))
		style.configure(
			"Modern.TButton",
			font=("Helvetica", 11, "bold"),
			padding=(14, 10),
			background="#2563eb",
			foreground="#ffffff",
			borderwidth=0,
		)
		style.map(
			"Modern.TButton",
			background=[("active", "#1d4ed8"), ("pressed", "#1e40af")],
			foreground=[("disabled", "#9ca3af")],
		)

	def _build_ui(self) -> None:
		outer = ttk.Frame(self.root, padding=24, style="Card.TFrame")
		outer.pack(fill="both", expand=True, padx=24, pady=24)

		ttk.Label(outer, text="Pack Creator", style="Title.TLabel").pack(anchor="w")
		ttk.Label(
			outer,
			text="Select vehicle folders, template and output location, then create your carpack.",
			style="Text.TLabel",
		).pack(anchor="w", pady=(8, 20))

		button_row = ttk.Frame(outer, style="Card.TFrame")
		button_row.pack(fill="x", pady=(0, 12))

		ttk.Button(button_row, text="Select Vehicles", style="Modern.TButton", command=self.select_folder).pack(side="left", padx=(0, 12))
		ttk.Button(button_row, text="Select Template", style="Modern.TButton", command=self.select_template).pack(side="left", padx=(0, 12))
		ttk.Button(button_row, text="Select Output", style="Modern.TButton", command=self.select_output).pack(side="left", padx=(0, 12))
		ttk.Button(button_row, text="Create Pack", style="Modern.TButton", command=self.create_pack_from_ui).pack(side="left")

		name_row = ttk.Frame(outer, style="Card.TFrame")
		name_row.pack(fill="x", pady=(0, 16))
		ttk.Label(name_row, text="Pack Name:", style="Text.TLabel").pack(side="left", padx=(0, 8))
		self.name_entry = ttk.Entry(name_row, width=40)
		self.name_entry.pack(side="left", fill="x", expand=True)

		self.folder_var = tk.StringVar(value="Vehicles: not selected")
		self.audioconfig_var = tk.StringVar(value="AudioConfig: not selected")
		self.sfx_var = tk.StringVar(value="SFX: not selected")
		self.manifest_var = tk.StringVar(value="fxmanifest.lua: not selected")
		self.output_var = tk.StringVar(value="Output folder: not selected")

		ttk.Label(outer, textvariable=self.folder_var, style="Text.TLabel", wraplength=600).pack(anchor="w", pady=(8, 8))
		ttk.Label(outer, textvariable=self.audioconfig_var, style="Text.TLabel", wraplength=600).pack(anchor="w", pady=(0, 8))
		ttk.Label(outer, textvariable=self.sfx_var, style="Text.TLabel", wraplength=600).pack(anchor="w", pady=(0, 8))
		ttk.Label(outer, textvariable=self.manifest_var, style="Text.TLabel", wraplength=600).pack(anchor="w", pady=(0, 8))
		ttk.Label(outer, textvariable=self.output_var, style="Text.TLabel", wraplength=600).pack(anchor="w")

	def select_folder(self) -> None:
		selected: list[str] = []

		while True:
			folder = filedialog.askdirectory(title="Select vehicle folder")
			if not folder:
				break

			if folder not in selected:
				selected.append(folder)

			add_more = messagebox.askyesno("Add Another", "Do you want to add another vehicle folder?")
			if not add_more:
				break

		if selected:
			self.selected_folders = selected
			if len(selected) == 1:
				self.folder_var.set(f"1 Vehicle: {selected[0]}")
			else:
				self.folder_var.set(f"{len(selected)} Vehicles selected")

	def select_template(self) -> None:
		folder = filedialog.askdirectory(title="Select a template folder or component")
		if not folder:
			return

		folder_path = Path(folder)

		audioconfig_candidate = folder_path / "audioconfig"
		sfx_candidate = folder_path / "sfx"
		manifest_candidate = folder_path / "fxmanifest.lua"

		if audioconfig_candidate.is_dir() and sfx_candidate.is_dir() and manifest_candidate.is_file():
			self.audioconfig_path = str(audioconfig_candidate)
			self.sfx_path = str(sfx_candidate)
			self.fxmanifest_path = str(manifest_candidate)

			self.audioconfig_var.set(f"AudioConfig: {audioconfig_candidate.name}")
			self.sfx_var.set(f"SFX: {sfx_candidate.name}")
			self.manifest_var.set(f"fxmanifest.lua: {manifest_candidate.name}")

			messagebox.showinfo("Done", "All components automatically detected!")
			return

		folder_name = folder_path.name.lower()

		if "audio" in folder_name:
			self.audioconfig_path = folder
			self.audioconfig_var.set(f"AudioConfig: {folder_path.name}")
			messagebox.showinfo("audioconfig", "audioconfig folder saved. Now select sfx folder.")
		elif "sfx" in folder_name:
			self.sfx_path = folder
			self.sfx_var.set(f"SFX: {folder_path.name}")
			messagebox.showinfo("sfx", "sfx folder saved. Now select fxmanifest.lua or audioconfig.")
		elif "manifest" in folder_name or "fxmanifest" in folder_name:
			manifest_file = folder_path / "fxmanifest.lua"
			if manifest_file.is_file():
				self.fxmanifest_path = str(manifest_file)
				self.manifest_var.set(f"fxmanifest.lua: {manifest_file.name}")
				messagebox.showinfo("manifest", "fxmanifest.lua found. Now select audioconfig and sfx.")
			else:
				messagebox.showwarning("Error", "fxmanifest.lua not found in this folder.")
		else:
			messagebox.showwarning("Not recognized", f"Folder '{folder_name}' could not be automatically assigned.\n\nPlease rename it or select a folder with 'audioconfig', 'sfx' or 'fxmanifest' in the name.")

	def select_output(self) -> None:
		folder = filedialog.askdirectory(title="Select output folder for carpack")
		if folder:
			self.output_folder = folder
			self.output_var.set(f"Output folder: {folder}")

	def create_pack_from_ui(self) -> None:
		if not self.selected_folders:
			messagebox.showerror("Missing Vehicles", "Please first select vehicle folders with 'Select Vehicles'.")
			return

		if not self.audioconfig_path:
			messagebox.showerror("Missing AudioConfig", "Please first select audioconfig folder with 'Select Template'.")
			return

		if not self.sfx_path:
			messagebox.showerror("Missing SFX", "Please first select sfx folder with 'Select Template'.")
			return

		if not self.fxmanifest_path:
			messagebox.showerror("Missing fxmanifest", "Please first select fxmanifest.lua file with 'Select Template'.")
			return

		if not self.output_folder:
			messagebox.showerror("Missing Output", "Please first select output folder with 'Select Output'.")
			return

		pack_name = (self.name_entry.get().strip() or None) if self.name_entry else None

		try:
			pack_path = create_carpack(
				vehicle_folders=self.selected_folders,
				output_folder=self.output_folder,
				pack_name=pack_name,
				audioconfig_path=self.audioconfig_path,
				sfx_path=self.sfx_path,
				fxmanifest_path=self.fxmanifest_path,
			)
		except Exception as exc:
			messagebox.showerror("Error", f"Could not create pack:\n{exc}")
			return

		messagebox.showinfo("Success", f"Pack successfully created:\n{pack_path}")


def main() -> None:
	root = tk.Tk()
	PackCreatorApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()
