"""Pack creator with Tkinter GUI and reusable create_pack function."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import zipfile
import customtkinter as ctk
import re


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
	def __init__(self, root: ctk.CTk) -> None:
		self.root = root
		self.root.title("Pack Creator - DC Carpack Builder")
		self.root.geometry("950x800")
		self.root.minsize(700, 500)
		
		# State
		self.selected_folders: list[str] = []
		self.output_folder: str | None = None
		self.audioconfig_path: str | None = None
		self.sfx_path: str | None = None
		self.fxmanifest_path: str | None = None
		self.name_entry: ctk.CTkEntry | None = None
		self.create_btn: ctk.CTkButton | None = None
		self.validation_hint: ctk.CTkLabel | None = None
		
		# Status cards
		self.status_cards: dict[str, tuple[ctk.CTkFrame, ctk.CTkFrame, ctk.CTkLabel]] = {}
		self.step_labels: list[ctk.CTkLabel] = []

		self._setup_style()
		self._build_ui()

	def _setup_style(self) -> None:
		ctk.set_appearance_mode("dark")
		self.root.configure(fg_color="#1a1a1a")

	def _is_valid(self) -> bool:
		"""Check if all required fields are filled and valid."""
		if not self.name_entry:
			return False
		pack_name = self.name_entry.get().strip().lower()
		name_valid = bool(pack_name) and re.match(r"^[a-z0-9_]+$", pack_name)
		
		return (
			len(self.selected_folders) > 0 and
			self.audioconfig_path is not None and
			self.sfx_path is not None and
			self.fxmanifest_path is not None and
			self.output_folder is not None and
			name_valid
		)

	def _update_create_button(self) -> None:
		"""Update Create Pack button state."""
		if self.create_btn:
			is_valid = self._is_valid()
			self.create_btn.configure(state="normal" if is_valid else "disabled")
			self.create_btn.configure(
				fg_color="#a91815" if is_valid else "#555555",
				hover_color="#8e1412" if is_valid else "#555555",
				border_color="#a91815" if is_valid else "#555555"
			)

	def _build_ui(self) -> None:
		outer = ctk.CTkFrame(self.root, fg_color="#1a1a1a", corner_radius=0)
		outer.pack(fill="both", expand=True, padx=24, pady=24)

		# Header
		ctk.CTkLabel(outer, text="DC Cars Carpack Creator", text_color="#a91815", font=("Helvetica", 24, "bold")).pack(anchor="w")
		ctk.CTkLabel(
			outer,
			text="4-step process to create a carpack",
			text_color="#888888",
			font=("Helvetica", 11),
		).pack(anchor="w", pady=(4, 20))

		# Step Indicator
		step_frame = ctk.CTkFrame(outer, fg_color="#1a1a1a", corner_radius=0)
		step_frame.pack(fill="x", pady=(0, 20))
		
		self.step_labels = []
		step_names = ["Vehicles", "Template", "Output", "Create"]
		for i, label in enumerate(step_names, 1):
			step_label = ctk.CTkLabel(
				step_frame,
				text=f"[{i}] {label}",
				text_color="#888888",
				font=("Helvetica", 10),
			)
			step_label.pack(side="left", padx=(0, 20))
			self.step_labels.append(step_label)

		# Selection Buttons (2 rows)
		button_row1 = ctk.CTkFrame(outer, fg_color="#1a1a1a", corner_radius=0)
		button_row1.pack(fill="x", pady=(0, 8))

		ctk.CTkButton(
			button_row1,
			text="1. Select Vehicles",
			command=self.select_folder,
			fg_color="#a91815",
			hover_color="#8e1412",
			text_color="#ffffff",
			border_width=2,
			border_color="#a91815",
			corner_radius=12,
			height=40,
			font=("Helvetica", 11, "bold"),
		).pack(side="left", padx=(0, 8), fill="x", expand=True)
		
		ctk.CTkButton(
			button_row1,
			text="2. Select Template",
			command=self.select_template,
			fg_color="#a91815",
			hover_color="#8e1412",
			text_color="#ffffff",
			border_width=2,
			border_color="#a91815",
			corner_radius=12,
			height=40,
			font=("Helvetica", 11, "bold"),
		).pack(side="left", fill="x", expand=True)

		button_row2 = ctk.CTkFrame(outer, fg_color="#1a1a1a", corner_radius=0)
		button_row2.pack(fill="x", pady=(0, 16))

		ctk.CTkButton(
			button_row2,
			text="3. Select Output",
			command=self.select_output,
			fg_color="#a91815",
			hover_color="#8e1412",
			text_color="#ffffff",
			border_width=2,
			border_color="#a91815",
			corner_radius=12,
			height=40,
			font=("Helvetica", 11, "bold"),
		).pack(side="left", padx=(0, 8), fill="x", expand=True)
		
		self.create_btn = ctk.CTkButton(
			button_row2,
			text="4. Create Pack",
			command=self.create_pack_from_ui,
			fg_color="#555555",
			hover_color="#555555",
			text_color="#ffffff",
			border_width=2,
			border_color="#555555",
			corner_radius=12,
			height=40,
			font=("Helvetica", 11, "bold"),
			state="disabled",
		)
		self.create_btn.pack(side="left", fill="x", expand=True)

		# Pack name input with validation
		name_card = ctk.CTkFrame(outer, fg_color="#242424", corner_radius=12, border_width=2, border_color="#a91815")
		name_card.pack(fill="x", pady=(0, 8))
		name_row = ctk.CTkFrame(name_card, fg_color="#242424", corner_radius=0)
		name_row.pack(fill="x", padx=12, pady=10)
		ctk.CTkLabel(name_row, text="Pack Name:", text_color="#a91815", font=("Helvetica", 11)).pack(side="left", padx=(0, 8))
		self.name_entry = ctk.CTkEntry(
			name_row,
			fg_color="#1a1a1a",
			text_color="#a91815",
			border_color="#a91815",
			border_width=2,
			placeholder_text="Example: xyz_dccars"
		)
		self.name_entry.pack(side="left", fill="x", expand=True)
		self.name_entry.bind("<KeyRelease>", lambda e: self._on_name_change())

		# Validation hint
		self.validation_hint = ctk.CTkLabel(
			outer,
			text="",
			text_color="#ff6666",
			font=("Helvetica", 9),
		)
		self.validation_hint.pack(anchor="w", pady=(0, 12))

		# Status Summary Cards
		summary_label = ctk.CTkLabel(outer, text="Status Summary", text_color="#a91815", font=("Helvetica", 12, "bold"))
		summary_label.pack(anchor="w", pady=(8, 8))

		summary_frame = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
		summary_frame.pack(fill="both", expand=True)

		self.folder_var = tk.StringVar(value="Vehicles: not selected")
		self.audioconfig_var = tk.StringVar(value="AudioConfig: not selected")
		self.sfx_var = tk.StringVar(value="SFX: not selected")
		self.manifest_var = tk.StringVar(value="fxmanifest.lua: not selected")
		self.output_var = tk.StringVar(value="Output folder: not selected")

		self.status_cards["folder"] = self._create_status_card(summary_frame, self.folder_var, False)
		self.status_cards["audioconfig"] = self._create_status_card(summary_frame, self.audioconfig_var, False)
		self.status_cards["sfx"] = self._create_status_card(summary_frame, self.sfx_var, False)
		self.status_cards["manifest"] = self._create_status_card(summary_frame, self.manifest_var, False)
		self.status_cards["output"] = self._create_status_card(summary_frame, self.output_var, False)

	def _on_name_change(self) -> None:
		"""Validate pack name on change."""
		if not self.name_entry:
			return
		
		pack_name = self.name_entry.get().strip().lower()
		
		# Remove invalid characters
		valid_name = re.sub(r"[^a-z0-9_]", "", pack_name)
		if valid_name != pack_name:
			self.name_entry.delete(0, tk.END)
			self.name_entry.insert(0, valid_name)
		
		# Update validation hint and button
		if pack_name and valid_name != pack_name:
			self.validation_hint.configure(text="⚠ Only a-z, 0-9, and _ allowed")
		else:
			self.validation_hint.configure(text="")
		
		self._update_create_button()

	def _create_status_card(self, parent: ctk.CTkFrame, text_var: tk.StringVar, is_selected: bool) -> tuple[ctk.CTkFrame, ctk.CTkFrame, ctk.CTkLabel]:
		"""Create a status card with colored background."""
		bg_color = "#1b3a1b" if is_selected else "#3a1b1b"
		border_color = "#00dd00" if is_selected else "#a91815"
		icon = "🟢" if is_selected else "🔴"
		
		card = ctk.CTkFrame(parent, fg_color=bg_color, corner_radius=10, border_width=2, border_color=border_color)
		card.pack(fill="x", padx=0, pady=6)
		
		content = ctk.CTkFrame(card, fg_color=bg_color, corner_radius=0)
		content.pack(fill="x", padx=12, pady=10)
		
		label = ctk.CTkLabel(
			content,
			text=f"{icon} {text_var.get()}",
			text_color=border_color,
			font=("Helvetica", 11),
			anchor="w",
			justify="left",
		)
		label.pack(fill="x")
		
		return (card, content, label)

	def _update_status_card(self, card_key: str, text_var: tk.StringVar, is_selected: bool) -> None:
		"""Update status card appearance and text."""
		card, content, label = self.status_cards[card_key]
		bg_color = "#1b3a1b" if is_selected else "#3a1b1b"
		border_color = "#00dd00" if is_selected else "#a91815"
		icon = "🟢" if is_selected else "🔴"
		
		card.configure(fg_color=bg_color, border_color=border_color)
		content.configure(fg_color=bg_color)
		label.configure(text=f"{icon} {text_var.get()}", text_color=border_color)
		
		# Update step indicator
		step_index = list(self.status_cards.keys()).index(card_key)
		if step_index < len(self.step_labels):
			self.step_labels[step_index].configure(text_color="#00dd00" if is_selected else "#888888")

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
			self._update_status_card("folder", self.folder_var, True)
			self._update_create_button()

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

			self._update_status_card("audioconfig", self.audioconfig_var, True)
			self._update_status_card("sfx", self.sfx_var, True)
			self._update_status_card("manifest", self.manifest_var, True)

			messagebox.showinfo("Done", "All components automatically detected!")
			self._update_create_button()
			return

		folder_name = folder_path.name.lower()

		if "audio" in folder_name:
			self.audioconfig_path = folder
			self.audioconfig_var.set(f"AudioConfig: {folder_path.name}")
			self._update_status_card("audioconfig", self.audioconfig_var, True)
			messagebox.showinfo("audioconfig", "audioconfig folder saved. Now select sfx folder.")
		elif "sfx" in folder_name:
			self.sfx_path = folder
			self.sfx_var.set(f"SFX: {folder_path.name}")
			self._update_status_card("sfx", self.sfx_var, True)
			messagebox.showinfo("sfx", "sfx folder saved. Now select fxmanifest.lua or audioconfig.")
		elif "manifest" in folder_name or "fxmanifest" in folder_name:
			manifest_file = folder_path / "fxmanifest.lua"
			if manifest_file.is_file():
				self.fxmanifest_path = str(manifest_file)
				self.manifest_var.set(f"fxmanifest.lua: {manifest_file.name}")
				self._update_status_card("manifest", self.manifest_var, True)
				messagebox.showinfo("manifest", "fxmanifest.lua found. Now select audioconfig and sfx.")
			else:
				messagebox.showwarning("Error", "fxmanifest.lua not found in this folder.")
		else:
			messagebox.showwarning("Not recognized", f"Folder '{folder_name}' could not be automatically assigned.\n\nPlease rename it or select a folder with 'audioconfig', 'sfx' or 'fxmanifest' in the name.")
		
		self._update_create_button()

	def select_output(self) -> None:
		folder = filedialog.askdirectory(title="Select output folder for carpack")
		if folder:
			self.output_folder = folder
			self.output_var.set(f"Output folder: {folder}")
			self._update_status_card("output", self.output_var, True)
			self._update_create_button()

	def create_pack_from_ui(self) -> None:
		if not self._is_valid():
			messagebox.showerror("Invalid Input", "Please fill all required fields correctly.")
			return

		pack_name = self.name_entry.get().strip().lower() if self.name_entry else None

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

		# Success message
		result = messagebox.showinfo(
			"Success",
			f"✓ Pack successfully created!\n\nLocation:\n{pack_path}\n\n[OK] to close"
		)
		
		# Optional: Reset after success
		if messagebox.askyesno("New Pack?", "Create another pack?"):
			self._reset_all()

	def _reset_all(self) -> None:
		"""Reset all selections."""
		self.selected_folders = []
		self.output_folder = None
		self.audioconfig_path = None
		self.sfx_path = None
		self.fxmanifest_path = None
		if self.name_entry:
			self.name_entry.delete(0, tk.END)

		self.folder_var.set("Vehicles: not selected")
		self.audioconfig_var.set("AudioConfig: not selected")
		self.sfx_var.set("SFX: not selected")
		self.manifest_var.set("fxmanifest.lua: not selected")
		self.output_var.set("Output folder: not selected")

		self._update_status_card("folder", self.folder_var, False)
		self._update_status_card("audioconfig", self.audioconfig_var, False)
		self._update_status_card("sfx", self.sfx_var, False)
		self._update_status_card("manifest", self.manifest_var, False)
		self._update_status_card("output", self.output_var, False)
		
		self._update_create_button()


def main() -> None:
	root = ctk.CTk()
	PackCreatorApp(root)
	root.mainloop()


if __name__ == "__main__":
	main()
