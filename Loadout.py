import tkinter as tk
import random
import json
from pathlib import Path

# --- Core Data ---
MELEE_WEAPONS = ["Cleaver", "Sickle", "Fists"]
WEAPONS = [
    "None", "Makarov PM", "Sawed-off Revolver", "TT33", "Bizon", "Carl Gustaf M45", "MP40",
    "CR-61 Skorpion", "Spectre M4", "PP-91 Kedr", "Thompson M1A1", "Criket", "PPSH",
    "Sporter 22", "BK-18", "Sawed-off BK-12", "Henry Single Shot", "Toz-34",
    "Mossberg 88", "BK-43", "Sawed-off BK-43", "Mossberg 590", "Mossberg 500",
    "Toz-34 sawed-off", "Winchester 1873", "Repeater Carbine", "Rusty AK-74",
    "Rusty AKS-74U", "AKS-74UN", "Rusty AKM", "CZ SA Vz.58", "SK 59/66"
]
MAGAZINES = ["None"] + [f"{i} Magazine" + ("s" if i > 1 else "") for i in range(1, 7)]
AMMO_STACKS = ["None"] + [f"{i} Stack" + ("s" if i > 1 else "") for i in range(1, 6)]
ARMOUR_TIERS = ["None", "Cloth", "Kevlar", "Ceramic"]
FILTERS = ["None", 200, 400, 600, 800]

# --- Detailed Data with weights (item, weight) ---

MEDICINE_CHOICES = [
    ("None", 6),
    ("B190 (small pack)", 3),
    ("B190 (big pack)", 1),
    ("Mexamin (small pack)", 2),
    ("Mexamin (big pack)", 1),
    ("B190 + Mexamin combo", 1),
    ("Expired Tramadol", 2),
    ("Empty pill bottle", 2),
]

BANDAGE_CHOICES = [
    ("None", 4),
    ("Bandage", 3),
    ("Small quick bandage (1 use)", 3),
    ("Big quick bandage", 2),
    ("Rags (damaged)", 4),
    ("Rags (pristine)", 2),
    ("Used bandage (Probably used to wipe something)", 1),
]

MEDKIT_CHOICES = [
    ("Big orange medkit (full)", 1),
    ("Small orange medkit", 2),
    ("Small blue medkit", 4),
    ("Small yellow medkit", 2),
    ("Coke and heroin", 5),
    ("Coke", 2),
    ("Heroin", 2),
    ("Empty syringe", 1),
    ("Spoon", 2),
    ("You think I can afford medkits?", 5),
]

FOOD_CHOICES = [
    ("None", 3),
    ("Zagorsky", 3),
    ("Klbasa", 3),
    ("Vodka (real men don't need food)", 2),
    ("Pasta live (cold)", 2),
    ("Cannibal breakfast (human meat)", 1),
    ("Mystery can (unlabeled)", 2),
]

WATER_CHOICES = [
    ("No water", 4),
    ("Half canteen (seems someone shot your canteen)", 3),
    ("Rusty canteen (half)", 2),
    ("Plastic bottle (full)", 3),
    ("Full canteen", 2),
    ("Vodka bottle filled with water", 1),
]

PACK_CHOICES = [
    ("Nothing", 5),
    ("Whetstone set", 2),
    ("5V battery", 3),
    ("9V battery", 3),
    ("Compass", 2),
    ("Old PDA (broken)", 2),
    ("Cigarette pack", 2),
    ("Lighter", 2),
]

GASMASK_CHOICES = [
    ("No mask", 5),
    ("GP5", 3),
    ("GP7", 2),
    ("Standard gasmask", 2),
    ("Cracked gasmask", 2),
    ("Filter canister only", 2),
]

POCKET_CHOICES = [
    ("Nothing but air", 4),
    ("Lighter", 3),
    ("Matches", 3),
    ("Spare loaded revolver", 1),
    ("Half a chocolate bar", 2),
    ("Cigarettes", 3),
    ("Mossberg Shotgun loaded", 4),
    ("Empty wallet", 2),
    ("Rusty bolts", 2),
]

RESTRAINT_CHOICES = [
    ("Nothing (I'll just knock them out)", 4),
    ("Zipties", 3),
    ("Rope", 3),
    ("Duct tape", 3),
]

CONFIG_PATH = Path(__file__).with_name("loadout_config.json")


def weighted_choice(choices):
    items, weights = zip(*choices)
    return random.choices(items, weights=weights, k=1)[0]


# --- Tooltip helper ---
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _event=None):
        if self.tip is not None:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + 20
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tip,
            text=self.text,
            bg="#222222",
            fg="#ffcccc",
            relief="solid",
            borderwidth=1,
            font=("Arial", 8),
        )
        label.pack(ipadx=4, ipady=2)

    def hide(self, _event=None):
        if self.tip is not None:
            self.tip.destroy()
            self.tip = None


class LoadoutApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Renegade Generator")
        self.root.geometry("560x720")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a1a")

        # Styles
        self.title_font = ("Arial", 16, "bold")
        self.text_font = ("Arial", 11, "bold")
        self.button_font = ("Arial", 11, "bold")
        self.exit_font = ("Arial", 10, "bold")

        self.color_fg = "#ff3333"
        self.color_text = "#ffcccc"
        self.color_accent = "#ff5555"
        self.btn_bg = "#330000"
        self.btn_fg = "#ff8888"
        self.btn_active_bg = "#660000"
        self.btn_active_fg = "#ffffff"

        # Lockable core fields
        self.fields = {
            "melee": None,
            "weapon": None,
            "magazines": None,
            "ammo": None,
            "armour": None,
            "filter": None,
            "money": None,
        }

        self.history = []  # list of full result strings

        self._build_ui()
        self.load_settings()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        if not self.result_box.get("1.0", tk.END).strip():
            self.set_result("Use Actions or Presets. Enable Detailed for full cursed immersion.")

    # --- UI setup ---
    def _build_ui(self):
        tk.Label(
            self.root,
            text="⚠️ Renegade Generator ⚠️",
            font=self.title_font,
            fg=self.color_fg,
            bg="#1a1a1a",
        ).pack(pady=(10, 5))

        # Include (Basic)
        include_frame = tk.LabelFrame(
            self.root,
            text="Include (Basic)",
            font=("Arial", 9, "bold"),
            fg=self.color_text,
            bg="#1a1a1a",
            bd=1,
            relief="ridge",
            labelanchor="n",
            padx=5,
            pady=3,
        )
        include_frame.pack(pady=(5, 4), fill="x")

        self.include_melee = tk.BooleanVar(value=True)
        self.include_weapon = tk.BooleanVar(value=True)
        self.include_armour = tk.BooleanVar(value=True)
        self.include_filter = tk.BooleanVar(value=True)
        self.include_money = tk.BooleanVar(value=True)

        self._make_check(include_frame, "Melee", self.include_melee, 0)
        self._make_check(include_frame, "Weapon", self.include_weapon, 1)
        self._make_check(include_frame, "Armour", self.include_armour, 2)
        self._make_check(include_frame, "Filter", self.include_filter, 3)
        self._make_check(include_frame, "Money", self.include_money, 4)

        # Lock (Basic)
        lock_frame = tk.LabelFrame(
            self.root,
            text="Lock (keep on reroll, Basic only)",
            font=("Arial", 9, "bold"),
            fg=self.color_text,
            bg="#1a1a1a",
            bd=1,
            relief="ridge",
            labelanchor="n",
            padx=5,
            pady=3,
        )
        lock_frame.pack(pady=(0, 4), fill="x")

        self.lock_melee = tk.BooleanVar(value=False)
        self.lock_weapon = tk.BooleanVar(value=False)
        self.lock_armour = tk.BooleanVar(value=False)
        self.lock_filter = tk.BooleanVar(value=False)
        self.lock_money = tk.BooleanVar(value=False)

        lock_widgets = [
            self._make_check(lock_frame, "Melee", self.lock_melee, 0),
            self._make_check(lock_frame, "Weapon + Ammo", self.lock_weapon, 1),
            self._make_check(lock_frame, "Armour", self.lock_armour, 2),
            self._make_check(lock_frame, "Filter", self.lock_filter, 3),
            self._make_check(lock_frame, "Money", self.lock_money, 4),
        ]
        lock_tips = [
            "Keep the current melee weapon on rerolls.",
            "Keep current weapon, magazines & ammo on rerolls.",
            "Keep current armour tier on rerolls.",
            "Keep current filter value on rerolls.",
            "Keep current money roll on rerolls.",
        ]
        for w, t in zip(lock_widgets, lock_tips):
            ToolTip(w, t)

        # Detailed toggles
        detailed_frame = tk.LabelFrame(
            self.root,
            text="Detailed (Optional)",
            font=("Arial", 9, "bold"),
            fg=self.color_text,
            bg="#1a1a1a",
            bd=1,
            relief="ridge",
            labelanchor="n",
            padx=5,
            pady=3,
        )
        detailed_frame.pack(pady=(0, 4), fill="x")

        self.include_medicine = tk.BooleanVar(value=False)
        self.include_bandages = tk.BooleanVar(value=False)
        self.include_medkits = tk.BooleanVar(value=False)
        self.include_food = tk.BooleanVar(value=False)
        self.include_water = tk.BooleanVar(value=False)
        self.include_pack = tk.BooleanVar(value=False)
        self.include_gasmask = tk.BooleanVar(value=False)
        self.include_pockets = tk.BooleanVar(value=False)
        self.include_restraints = tk.BooleanVar(value=False)

        self._make_check(detailed_frame, "Medicine", self.include_medicine, 0, row=0)
        self._make_check(detailed_frame, "Bandages", self.include_bandages, 1, row=0)
        self._make_check(detailed_frame, "Medkits", self.include_medkits, 2, row=0)
        self._make_check(detailed_frame, "Food", self.include_food, 3, row=0)
        self._make_check(detailed_frame, "Water", self.include_water, 4, row=0)

        self._make_check(detailed_frame, "Pack", self.include_pack, 0, row=1)
        self._make_check(detailed_frame, "Gasmask", self.include_gasmask, 1, row=1)
        self._make_check(detailed_frame, "Pockets", self.include_pockets, 2, row=1)
        self._make_check(detailed_frame, "Restraints", self.include_restraints, 3, row=1)

        # Result box
        result_frame = tk.Frame(self.root, bg="#1a1a1a")
        result_frame.pack(pady=(4, 4), fill="x")

        tk.Label(
            result_frame,
            text="Current Loadout:",
            font=("Arial", 10, "bold"),
            fg=self.color_text,
            bg="#1a1a1a",
        ).pack(anchor="w", padx=10)

        self.result_box = tk.Text(
            result_frame,
            height=12,
            width=70,
            bg="#111111",
            fg=self.color_accent,
            font=self.text_font,
            relief="solid",
            bd=1,
        )
        self.result_box.pack(padx=10, pady=(2, 5), fill="x")
        self.result_box.config(state="disabled")

        self.result_box.tag_configure("bad", foreground="#ff4444")
        self.result_box.tag_configure("good", foreground="#7CFC00")
        self.result_box.tag_configure("normal", foreground=self.color_accent)

        # Actions
        actions_frame = tk.LabelFrame(
            self.root,
            text="Actions",
            font=("Arial", 9, "bold"),
            fg=self.color_text,
            bg="#1a1a1a",
            bd=1,
            relief="ridge",
            labelanchor="n",
            padx=8,
            pady=6,
        )
        actions_frame.pack(pady=(0, 5), fill="x")

        for i in range(3):
            actions_frame.columnconfigure(i, weight=1)

        self._make_button(actions_frame, "Generate Basic", self.generate_loadout, width=16)\
            .grid(row=0, column=0, padx=4, pady=3, sticky="nsew")
        self._make_button(actions_frame, "Generate Detailed", self.generate_detailed, width=16)\
            .grid(row=0, column=1, padx=4, pady=3, sticky="nsew")
        self._make_button(actions_frame, "Generate All", self.generate_all, width=16)\
            .grid(row=0, column=2, padx=4, pady=3, sticky="nsew")

        self._make_button(actions_frame, "Generate Money Only", self.generate_money, width=16)\
            .grid(row=1, column=0, padx=4, pady=3, sticky="nsew")
        self._make_button(actions_frame, "Copy", self.copy_to_clipboard, width=16)\
            .grid(row=1, column=1, padx=4, pady=3, sticky="nsew")
        self._make_button(actions_frame, "Clear / Reset", self.clear_all, width=16)\
            .grid(row=1, column=2, padx=4, pady=3, sticky="nsew")

        # Presets
        presets_frame = tk.LabelFrame(
            self.root,
            text="Presets",
            font=("Arial", 9, "bold"),
            fg=self.color_text,
            bg="#1a1a1a",
            bd=1,
            relief="ridge",
            labelanchor="n",
            padx=5,
            pady=3,
        )
        presets_frame.pack(pady=(3, 5), fill="x")

        for i in range(3):
            presets_frame.columnconfigure(i, weight=1)

        # Row 0
        self._make_button(presets_frame, "Scuffed Raider", self.preset_scuffed_raider, width=16)\
            .grid(row=0, column=0, padx=5, pady=3, sticky="nsew")
        self._make_button(presets_frame, "Rich Junkie", self.preset_rich_pmc, width=16)\
            .grid(row=0, column=1, padx=5, pady=3, sticky="nsew")
        self._make_button(presets_frame, "Swamp Goblin", self.preset_swamp_goblin, width=16)\
            .grid(row=0, column=2, padx=5, pady=3, sticky="nsew")

        # Row 1
        self._make_button(presets_frame, "Hungover", self.preset_hungover, width=16)\
            .grid(row=1, column=0, padx=5, pady=3, sticky="nsew")
        self._make_button(presets_frame, "Desperate Muppet", self.preset_desperate_rookie, width=16)\
            .grid(row=1, column=1, padx=5, pady=3, sticky="nsew")
        self._make_button(presets_frame, "Crack Medic", self.preset_field_medic, width=16)\
            .grid(row=1, column=2, padx=5, pady=3, sticky="nsew")

        # History
        # history_frame = tk.LabelFrame(
        #     self.root,
        #     text="History (last 10)",
        #     font=("Arial", 9, "bold"),
        #     fg=self.color_text,
        #     bg="#1a1a1a",
        #     bd=1,
        #     relief="ridge",
        #     labelanchor="n",
        #     padx=5,
        #     pady=3,
        # )
        # history_frame.pack(pady=(4, 0), fill="both", expand=True)

        # self.history_listbox = tk.Listbox(
        #     history_frame,
        #     width=70,
        #     height=7,
        #     bg="#111111",
        #     fg=self.color_text,
        #     selectbackground="#330000",
        #     highlightthickness=0,
        #     activestyle="none",
        # )
        # self.history_listbox.pack(padx=8, pady=5, fill="both", expand=True)

        # # Restore from history on double-click / Enter
        # self.history_listbox.bind("<Double-Button-1>", self.on_history_activate)
        # self.history_listbox.bind("<Return>", self.on_history_activate)

        # Exit button
        tk.Button(
            self.root,
            text="Exit",
            command=self.on_close,
            font=self.exit_font,
            bg=self.btn_bg,
            fg=self.btn_fg,
            activebackground=self.btn_active_bg,
            activeforeground=self.btn_active_fg,
            width=12,
        ).pack(pady=(4, 8))

    # --- UI helpers ---
    def _make_button(self, parent, text, command, width=18):
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=self.button_font,
            bg=self.btn_bg,
            fg=self.btn_fg,
            activebackground=self.btn_active_bg,
            activeforeground=self.btn_active_fg,
            width=width,
        )

    def _make_check(self, parent, label, var, col, row=0):
        cb = tk.Checkbutton(
            parent,
            text=label,
            variable=var,
            font=("Arial", 9),
            bg="#1a1a1a",
            fg=self.color_text,
            selectcolor="#330000",
            activebackground="#1a1a1a",
            activeforeground=self.color_fg,
            pady=0,
        )
        cb.grid(row=row, column=col, padx=4, pady=1, sticky="w")
        return cb

    # --- Settings ---
    def get_settings(self):
        return {
            "include": {
                "melee": self.include_melee.get(),
                "weapon": self.include_weapon.get(),
                "armour": self.include_armour.get(),
                "filter": self.include_filter.get(),
                "money": self.include_money.get(),
                "medicine": self.include_medicine.get(),
                "bandages": self.include_bandages.get(),
                "medkits": self.include_medkits.get(),
                "food": self.include_food.get(),
                "water": self.include_water.get(),
                "pack": self.include_pack.get(),
                "gasmask": self.include_gasmask.get(),
                "pockets": self.include_pockets.get(),
                "restraints": self.include_restraints.get(),
            },
            "lock": {
                "melee": self.lock_melee.get(),
                "weapon": self.lock_weapon.get(),
                "armour": self.lock_armour.get(),
                "filter": self.lock_filter.get(),
                "money": self.lock_money.get(),
            },
        }

    def apply_settings(self, data):
        inc = data.get("include", {})
        self.include_melee.set(inc.get("melee", True))
        self.include_weapon.set(inc.get("weapon", True))
        self.include_armour.set(inc.get("armour", True))
        self.include_filter.set(inc.get("filter", True))
        self.include_money.set(inc.get("money", True))

        self.include_medicine.set(inc.get("medicine", False))
        self.include_bandages.set(inc.get("bandages", False))
        self.include_medkits.set(inc.get("medkits", False))
        self.include_food.set(inc.get("food", False))
        self.include_water.set(inc.get("water", False))
        self.include_pack.set(inc.get("pack", False))
        self.include_gasmask.set(inc.get("gasmask", False))
        self.include_pockets.set(inc.get("pockets", False))
        self.include_restraints.set(inc.get("restraints", False))

        locks = data.get("lock", {})
        self.lock_melee.set(locks.get("melee", False))
        self.lock_weapon.set(locks.get("weapon", False))
        self.lock_armour.set(locks.get("armour", False))
        self.lock_filter.set(locks.get("filter", False))
        self.lock_money.set(locks.get("money", False))

    def save_settings(self):
        try:
            CONFIG_PATH.write_text(json.dumps(self.get_settings(), indent=2), encoding="utf-8")
        except Exception:
            pass

    def load_settings(self):
        if not CONFIG_PATH.exists():
            return
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            self.apply_settings(data)
        except Exception:
            pass

    # --- Result rendering ---
    def set_result(self, text: str):
        self.result_box.config(state="normal")
        self.result_box.delete("1.0", tk.END)
        for line in text.splitlines():
            tag = self.get_line_tag(line)
            self.result_box.insert(tk.END, line + "\n", tag)
        self.result_box.config(state="disabled")

    def get_line_tag(self, line: str) -> str:
        ll = line.lower()
        if (
            "none" in ll
            or "rusty" in ll
            or "0 ru" in ll
            or "you think i can afford medkits" in ll
            or "cannibal breakfast" in ll
            or "rotten" in ll
        ):
            return "bad"
        good_keywords = [
            "kevlar", "ceramic", "ak-", "aks", "mossberg", "vz.58",
            "ppsh", "full canteen", "gasmask", "big orange medkit (full)"
        ]
        if any(k in ll for k in good_keywords):
            return "good"
        return "normal"

    # --- History ---
    # def add_to_history(self, text: str):
    #     text = text.strip()
    #     if not text:
    #         return
    #     # avoid duplicating identical last entry
    #     if self.history and self.history[0] == text:
    #         return
    #     self.history.insert(0, text)
    #     if len(self.history) > 10:
    #         self.history = self.history[:10]
    #     self.refresh_history()

    # def refresh_history(self):
    #     self.history_listbox.delete(0, tk.END)
    #     for i, item in enumerate(self.history, start=1):
    #         preview = item.replace("\n", " | ")
    #         if len(preview) > 140:
    #             preview = preview[:137] + "..."
    #         self.history_listbox.insert(tk.END, f"{i}. {preview}")

    # def on_history_activate(self, event=None):
    #     sel = self.history_listbox.curselection()
    #     if not sel:
    #         return
    #     idx = sel[0]
    #     if 0 <= idx < len(self.history):
    #         self.set_result(self.history[idx])

    # --- Basic generators ---
    def generate_loadout(self):
        parts = []

        if self.include_melee.get():
            melee = self.fields["melee"] if self.lock_melee.get() and self.fields["melee"] is not None \
                else random.choice(MELEE_WEAPONS)
            self.fields["melee"] = melee
            parts.append(f"Melee: {melee}")

        if self.include_weapon.get():
            if self.lock_weapon.get() and self.fields["weapon"] is not None:
                weapon = self.fields["weapon"]
                magazines = self.fields["magazines"]
                ammo = self.fields["ammo"]
            else:
                weapon = random.choice(WEAPONS)
                magazines = random.choice(MAGAZINES)
                ammo = random.choice(AMMO_STACKS)
                self.fields["weapon"] = weapon
                self.fields["magazines"] = magazines
                self.fields["ammo"] = ammo
            parts.append(f"Weapon: {weapon}")
            parts.append(f"Magazines: {magazines}")
            parts.append(f"Ammo: {ammo}")

        if self.include_armour.get():
            armour = self.fields["armour"] if self.lock_armour.get() and self.fields["armour"] is not None \
                else random.choice(ARMOUR_TIERS)
            self.fields["armour"] = armour
            parts.append(f"Armour: {armour}")

        if self.include_filter.get():
            filt = self.fields["filter"] if self.lock_filter.get() and self.fields["filter"] is not None \
                else random.choice(FILTERS)
            self.fields["filter"] = filt
            parts.append(f"Filter: {filt}")

        # generate/store money for locking/consistency, but don't display it in basic gen
        self._ensure_money_generated()

        if not parts:
            parts.append("No basic categories selected.")

        text = "\n".join(parts)
        self.set_result(text)
        # self.add_to_history(text)

    def generate_money(self):
        if not self.include_money.get():
            self.set_result("Money generation is disabled.")
            return

        money = self.fields["money"] if self.lock_money.get() and self.fields["money"] is not None \
            else random.randrange(0, 150_001, 5_000)
        self.fields["money"] = money

        text = f"Money: {money} RU"
        self.set_result(text)
        # self.add_to_history(text)

    # Ensure money gets generated/stored for basic/detailed gens (but not displayed)
    def _ensure_money_generated(self):
        if not self.include_money.get():
            return
        # if money is locked and already present, keep it
        if self.lock_money.get() and self.fields.get("money") is not None:
            return
        # generate and store (step is 5000)
        self.fields["money"] = random.randrange(0, 150_001, 5_000)

    # --- Detailed generator ---
    def _build_detailed_parts(self):
        parts = []
        if self.include_medicine.get():
            parts.append(f"Medicine: {weighted_choice(MEDICINE_CHOICES)}")
        if self.include_bandages.get():
            parts.append(f"Bandages: {weighted_choice(BANDAGE_CHOICES)}")
        if self.include_medkits.get():
            parts.append(f"Medkits: {weighted_choice(MEDKIT_CHOICES)}")
        if self.include_food.get():
            parts.append(f"Food: {weighted_choice(FOOD_CHOICES)}")
        if self.include_water.get():
            parts.append(f"Water: {weighted_choice(WATER_CHOICES)}")
        if self.include_pack.get():
            parts.append(f"Pack: {weighted_choice(PACK_CHOICES)}")
        if self.include_gasmask.get():
            parts.append(f"Gasmask: {weighted_choice(GASMASK_CHOICES)}")
        if self.include_pockets.get():
            parts.append(f"Pockets: {weighted_choice(POCKET_CHOICES)}")
        if self.include_restraints.get():
            parts.append(f"Restraints: {weighted_choice(RESTRAINT_CHOICES)}")
        return parts

    def generate_detailed(self):
        parts = self._build_detailed_parts()
        # generate/store money for locking/consistency, but don't display here
        self._ensure_money_generated()
        if not parts:
            parts.append("No detailed categories selected.")
        text = "\n".join(parts)
        self.set_result(text)
        # self.add_to_history(text)

    # --- All-in-one ---
    def generate_all(self):
        parts = []

        # Basic
        if self.include_melee.get():
            melee = self.fields["melee"] if self.lock_melee.get() and self.fields["melee"] is not None \
                else random.choice(MELEE_WEAPONS)
            self.fields["melee"] = melee
            parts.append(f"Melee: {melee}")

        if self.include_weapon.get():
            if self.lock_weapon.get() and self.fields["weapon"] is not None:
                weapon = self.fields["weapon"]
                magazines = self.fields["magazines"]
                ammo = self.fields["ammo"]
            else:
                weapon = random.choice(WEAPONS)
                magazines = random.choice(MAGAZINES)
                ammo = random.choice(AMMO_STACKS)
                self.fields["weapon"] = weapon
                self.fields["magazines"] = magazines
                self.fields["ammo"] = ammo
            parts.append(f"Weapon: {weapon}")
            parts.append(f"Magazines: {magazines}")
            parts.append(f"Ammo: {ammo}")

        if self.include_armour.get():
            armour = self.fields["armour"] if self.lock_armour.get() and self.fields["armour"] is not None \
                else random.choice(ARMOUR_TIERS)
            self.fields["armour"] = armour
            parts.append(f"Armour: {armour}")

        if self.include_filter.get():
            filt = self.fields["filter"] if self.lock_filter.get() and self.fields["filter"] is not None \
                else random.choice(FILTERS)
            self.fields["filter"] = filt
            parts.append(f"Filter: {filt}")

        # Detailed
        parts.extend(self._build_detailed_parts())

        # Money
        if self.include_money.get():
            money = self.fields["money"] if self.lock_money.get() and self.fields["money"] is not None \
                else random.randrange(0, 150_001, 5_000)
            self.fields["money"] = money
            parts.append(f"Money: {money} RU")

        if not parts:
            parts.append("No categories selected.")

        text = "\n".join(parts)
        self.set_result(text)
        # self.add_to_history(text)

    # --- Presets ---

    def preset_scuffed_raider(self):
        self._preset_reset()
        self.include_melee.set(True)
        self.include_weapon.set(True)
        self.include_armour.set(True)
        self.include_filter.set(False)
        self.include_money.set(True)
        self.include_food.set(True)
        self.include_water.set(True)
        self.include_bandages.set(True)
        self.include_medicine.set(True)
        self.include_pockets.set(True)
        self.generate_all()

    def preset_rich_pmc(self):
        self._preset_reset()
        self.include_melee.set(True)
        self.include_weapon.set(True)
        self.include_armour.set(True)
        self.include_filter.set(True)
        self.include_money.set(True)
        self.include_medicine.set(True)
        self.include_medkits.set(True)
        self.include_food.set(True)
        self.include_water.set(True)
        self.include_pack.set(True)
        self.include_gasmask.set(True)
        self.include_pockets.set(True)

        weapon = random.choice([
            "AKS-74UN", "CZ SA Vz.58", "Mossberg 590", "Mossberg 500",
            "PPSH", "Spectre M4", "PP-91 Kedr"
        ])
        magazines = random.choice(MAGAZINES[2:])
        ammo = random.choice(AMMO_STACKS[2:])
        armour = random.choice(["Kevlar", "Ceramic"])
        filt = random.choice([400, 600, 800])
        money = random.randrange(80_000, 150_001, 5_000)

        self.fields.update({
            "melee": random.choice(MELEE_WEAPONS),
            "weapon": weapon,
            "magazines": magazines,
            "ammo": ammo,
            "armour": armour,
            "filter": filt,
            "money": money,
        })

        self.generate_all()

    def preset_swamp_goblin(self):
        self._preset_reset()
        self.include_melee.set(True)
        self.include_weapon.set(True)
        self.include_armour.set(True)
        self.include_filter.set(True)
        self.include_money.set(True)
        self.include_food.set(True)
        self.include_water.set(True)
        self.include_bandages.set(True)
        self.include_pockets.set(True)
        self.include_restraints.set(True)

        melee = random.choice(["Sickle", "Fists"])
        weapon = random.choice(["None", "Sporter 22", "Rusty AKM", "Rusty AK-74"])
        magazines = random.choice(MAGAZINES[:3])
        ammo = random.choice(AMMO_STACKS[:3])
        armour = random.choice(["None", "Cloth"])
        filt = random.choice(["None", 200])
        money = random.randrange(0, 40_001, 5_000)

        self.fields.update({
            "melee": melee,
            "weapon": weapon,
            "magazines": magazines,
            "ammo": ammo,
            "armour": armour,
            "filter": filt,
            "money": money,
        })

        self.generate_all()

    def preset_hungover(self):
        self._preset_reset()
        text = (
            "Preset: Hungover\n"
            "You partied so hard last night that you woke up in a ditch.\n"
            "A renegade stole your shoes. Best of luck.\n"
            "\n"
            "Melee: Vodka bottle\n"
            "Food: Vodka (real men don't need food)\n"
            "Water: No water\n"
            "Pockets: Empty wallet\n"
        )
        self.set_result(text)
        # self.add_to_history(text)

    def preset_desperate_rookie(self):
        self._preset_reset()
        self.include_melee.set(True)
        self.include_weapon.set(True)
        self.include_money.set(True)
        self.include_food.set(True)
        self.include_water.set(True)
        self.include_pockets.set(True)

        self.fields["melee"] = random.choice(["Fists", "Sickle"])
        self.fields["weapon"] = random.choice(["None", "Sporter 22", "BK-18"])
        self.fields["magazines"] = random.choice(["None", "1 Magazine"])
        self.fields["ammo"] = random.choice(
            ["None", "1 Stack", "Half a Stack", "1 Bullet (make it count)"]
        )
        self.fields["armour"] = "None"
        self.fields["filter"] = "None"
        # self.fields["money"] = random.randrange(0, 20_001, 5_000)

        text_parts = [
            "Preset: Desperate Rookie",
            "You're new, broke, and everyone can tell.",
            "",
            f"Melee: {self.fields['melee']}",
            f"Weapon: {self.fields['weapon']}",
            f"Magazines: {self.fields['magazines']}",
            f"Ammo: {self.fields['ammo']}",
            "Armour: None",
            "Filter: None",
            f"Food: {weighted_choice(FOOD_CHOICES)}",
            f"Water: {weighted_choice(WATER_CHOICES)}",
            f"Pockets: {weighted_choice(POCKET_CHOICES)}",
            # f"💰 Money: {self.fields['money']} RU",
        ]
        text = "\n".join(text_parts)
        self.set_result(text)
        # self.add_to_history(text)

    def preset_field_medic(self):
        self._preset_reset()
        self.include_melee.set(True)
        self.include_weapon.set(True)
        self.include_armour.set(True)
        self.include_medicine.set(True)
        self.include_bandages.set(True)
        self.include_medkits.set(True)
        self.include_pack.set(True)
        self.include_pockets.set(True)
        self.include_water.set(True)
        self.include_food.set(True)
        self.include_money.set(True)

        self.fields["melee"] = random.choice(["Fists", "Cleaver"])
        self.fields["weapon"] = random.choice(["Makarov PM", "TT33", "None"])
        self.fields["magazines"] = random.choice(["1 Magazine", "2 Magazines"])
        self.fields["ammo"] = random.choice(["1 Stack", "2 Stacks"])
        self.fields["armour"] = random.choice(["Cloth", "Kevlar"])
        self.fields["filter"] = random.choice(["None", 200])
        # self.fields["money"] = random.randrange(20_000, 60_001, 5_000)

        text_parts = [
            "Preset: Field Medic",
            "You're here to keep idiots alive, not win fashion contests.",
            "",
            f"Melee: {self.fields['melee']}",
            f"Sidearm: {self.fields['weapon']} ({self.fields['magazines']}, {self.fields['ammo']})",
            f"Armour: {self.fields['armour']}",
            f"Medicine: {weighted_choice(MEDICINE_CHOICES)}",
            f"Bandages: {weighted_choice(BANDAGE_CHOICES)}",
            f"Medkits: {weighted_choice(MEDKIT_CHOICES)}",
            f"Pack: {weighted_choice(PACK_CHOICES)}",
            f"Water: {weighted_choice(WATER_CHOICES)}",
            f"Pockets: {weighted_choice(POCKET_CHOICES)}",
            # f"Money: {self.fields['money']} RU",
        ]
        text = "\n".join(text_parts)
        self.set_result(text)
        # self.add_to_history(text)

    def _preset_reset(self):
        self.lock_melee.set(False)
        self.lock_weapon.set(False)
        self.lock_armour.set(False)
        self.lock_filter.set(False)
        self.lock_money.set(False)
        self.fields = {k: None for k in self.fields}

        self.include_medicine.set(False)
        self.include_bandages.set(False)
        self.include_medkits.set(False)
        self.include_food.set(False)
        self.include_water.set(False)
        self.include_pack.set(False)
        self.include_gasmask.set(False)
        self.include_pockets.set(False)
        self.include_restraints.set(False)

    # --- Misc ---
    def copy_to_clipboard(self):
        text = self.result_box.get("1.0", tk.END).strip()
        if not text:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def clear_all(self):
        self.include_melee.set(True)
        self.include_weapon.set(True)
        self.include_armour.set(True)
        self.include_filter.set(True)
        self.include_money.set(True)

        self.lock_melee.set(False)
        self.lock_weapon.set(False)
        self.lock_armour.set(False)
        self.lock_filter.set(False)
        self.lock_money.set(False)

        self.include_medicine.set(False)
        self.include_bandages.set(False)
        self.include_medkits.set(False)
        self.include_food.set(False)
        self.include_water.set(False)
        self.include_pack.set(False)
        self.include_gasmask.set(False)
        self.include_pockets.set(False)
        self.include_restraints.set(False)

        self.fields = {k: None for k in self.fields}
        self.history = []
        self.refresh_history()
        self.set_result("Cleared. Ready for a fresh roll.")
        self.save_settings()

    def on_close(self):
        self.save_settings()
        self.root.destroy()


def main():
    root = tk.Tk()
    LoadoutApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
