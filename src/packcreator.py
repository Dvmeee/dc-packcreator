"""Pack creator with Tkinter GUI and reusable create_pack function."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import zipfile


REQUIRED_PACK_FOLDERS = ("audioconfig", "data", "stream", "sfx")
DEFAULT_TEMPLATE_DIR = "xyz"
META_EXTENSIONS = {".meta"}
STREAM_EXTENSIONS = {
	".yft",
	".ytd",
	".ydr",
	".ydd",
	".ybn",
	".ymap",
	".ytyp",
	".ycd",
	".awc",
	".rel",
}


def _write_template_files(archive: zipfile.ZipFile, template_dir: Path) -> None:
	template_path = template_dir.expanduser().resolve()
	if not template_path.exists():
		raise FileNotFoundError(f"Template directory not found: {template_path}")
	if not template_path.is_dir():
		raise NotADirectoryError(f"Template path is not a directory: {template_path}")

	manifest_path = template_path / "fxmanifest.lua"
	if not manifest_path.is_file():
		raise FileNotFoundError(f"Missing fxmanifest.lua in template directory: {template_path}")

	audio_path = template_path / "audioconfig"
	if not audio_path.is_dir():
		raise FileNotFoundError(f"Missing audioconfig directory in template directory: {template_path}")

	archive.write(manifest_path, "fxmanifest.lua")

	for root, _, files in os.walk(audio_path):
		root_path = Path(root).resolve()
		relative_root = root_path.relative_to(audio_path)
		if not files and relative_root != Path("."):
			archive.writestr((Path("audioconfig") / relative_root).as_posix() + "/", "")

		for file_name in files:
			file_path = root_path / file_name
			target = Path("audioconfig") / relative_root / file_name
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
	template_dir: str = DEFAULT_TEMPLATE_DIR,
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

	with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
		for folder_name in REQUIRED_PACK_FOLDERS:
			archive.writestr(f"{folder_name}/", "")

		_write_template_files(archive, Path(template_dir))

		for vehicle_root in resolved_vehicle_folders:
			vehicle_name = vehicle_root.name
			for root, _, files in os.walk(vehicle_root):
				current_root = Path(root).resolve()
				for file_name in files:
					file_path = current_root / file_name
					if file_path.resolve() == zip_path:
						continue

					relative_file = file_path.relative_to(vehicle_root)
					extension = file_path.suffix.lower()

					if extension in META_EXTENSIONS:
						target_path = Path("data") / vehicle_name / relative_file
					elif extension in STREAM_EXTENSIONS:
						target_path = Path("stream") / vehicle_name / relative_file
					else:
						target_path = Path("stream") / vehicle_name / relative_file

					archive.write(file_path, target_path.as_posix())

	return str(zip_path)


class PackCreatorApp:
	def __init__(self, root: tk.Tk) -> None:
		self.root = root
		self.root.title("Pack Creator")
		self.root.geometry("560x320")
		self.root.minsize(520, 300)
		self.root.configure(bg="#f3f4f6")

		self.selected_folders: list[str] = []
		self.pack_name: str | None = None
		self.template_dir = str(Path.cwd() / DEFAULT_TEMPLATE_DIR)

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
			text="Wähle einen oder mehrere Fahrzeug-Ordner, gib optional einen Namen ein und erstelle dein Carpack.",
			style="Text.TLabel",
		).pack(anchor="w", pady=(8, 20))

		button_row = ttk.Frame(outer, style="Card.TFrame")
		button_row.pack(fill="x", pady=(0, 16))

		ttk.Button(button_row, text="Select folder", style="Modern.TButton", command=self.select_folder).pack(side="left", padx=(0, 12))
		ttk.Button(button_row, text="Enter Name", style="Modern.TButton", command=self.enter_name).pack(side="left", padx=(0, 12))
		ttk.Button(button_row, text="Create Pack", style="Modern.TButton", command=self.create_pack_from_ui).pack(side="left")

		self.folder_var = tk.StringVar(value="Keine Fahrzeugordner ausgewählt")
		self.name_var = tk.StringVar(value="Pack-Name: automatisch")

		ttk.Label(outer, textvariable=self.folder_var, style="Text.TLabel", wraplength=500).pack(anchor="w", pady=(8, 8))
		ttk.Label(outer, textvariable=self.name_var, style="Text.TLabel").pack(anchor="w")

	def select_folder(self) -> None:
		selected: list[str] = []

		while True:
			folder = filedialog.askdirectory(title="Select vehicle folder")
			if not folder:
				break

			if folder not in selected:
				selected.append(folder)

			add_more = messagebox.askyesno("Weitere Auswahl", "Möchtest du einen weiteren Fahrzeug-Ordner hinzufügen?")
			if not add_more:
				break

		if selected:
			self.selected_folders = selected
			if len(selected) == 1:
				self.folder_var.set(f"1 Fahrzeugordner: {selected[0]}")
			else:
				self.folder_var.set(f"{len(selected)} Fahrzeugordner ausgewählt")

	def enter_name(self) -> None:
		name = simpledialog.askstring("Enter Name", "Pack name (optional):", parent=self.root)
		if name is None:
			return

		cleaned_name = name.strip()
		self.pack_name = cleaned_name or None
		if self.pack_name:
			self.name_var.set(f"Pack-Name: {self.pack_name}")
		else:
			self.name_var.set("Pack-Name: automatisch")

	def create_pack_from_ui(self) -> None:
		if not self.selected_folders:
			messagebox.showerror("Missing folder", "Bitte zuerst mindestens einen Fahrzeug-Ordner mit 'Select folder' wählen.")
			return

		try:
			output_dir = Path.cwd() / "output"
			pack_path = create_carpack(
				vehicle_folders=self.selected_folders,
				output_folder=str(output_dir),
				pack_name=self.pack_name,
				template_dir=self.template_dir,
			)
		except Exception as exc:
			messagebox.showerror("Error", f"Pack konnte nicht erstellt werden:\n{exc}")
			return

		messagebox.showinfo("Success", f"Pack erfolgreich erstellt:\n{pack_path}")


def main() -> None:
	root = tk.Tk()
	PackCreatorApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()
