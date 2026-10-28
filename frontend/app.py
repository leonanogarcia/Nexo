import json
import re
import shutil
import sqlite3
from pathlib import Path
from datetime import date, datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

from backend import (
    paths,
    BASE_DIR, RESOURCE_DIR, USER_DATA_DIR, DATA_DIR, BACKUPS_DIR,
    CONFIG_PATH, DEFAULT_DB_PATH, DB_PATH, DOCS_DIR,
    ICON_PNG, LOGO_PNG, ICON_ICO, UI_ASSETS,
    load_file_config, save_file_config, get_db_path, set_db_path,
    db, now_iso, init_db, next_code, get_setting, set_setting,
    get_cost_settings, record_edit, list_names,
    UNITS_MASS, UNITS_VOLUME, UNITS_COUNT, UNITS, BASE_UNITS_DEFAULT,
    to_float, optional_float, money_to_float, fmt, fmt_num, normalize_text,
    dimension_of_unit, base_unit, unit_factor_to_default_base,
    configured_base_unit, unit_factor_to_internal,
    custom_units_for_material, conversion_to_base, convert_generic, conversion_between,
    material_cost, recipe_cost, item_cost, operational_cost,
    product_unit_cost, product_direct_cost, snapshot_costs,
    save_uploaded_document, latest_document,
    extract_docx_text, extract_pdf_text, parse_recipe_lines,
)
from .components import (
    _field_palette, rounded_entry, numeric_entry, masked_money_entry,
    safe_error, bind_text_capitalization, FlatEmojiButton,
    Modal, RoundedPanel, PillScrollbar, VerticalPillScrollbar,
    RoundedActionButton, RoundedEntry, SidebarIcon, NavItem,
    ReferenceSidebar, RoundedDropdown, CustomHistoryModal, ListDialog,
    get_work_area,
)
from .pages import (
    HomePageMixin, TableHelpersMixin, MaterialsPageMixin,
    RecipesPageMixin, ProductsPageMixin, SettingsPageMixin,
)


class App(
    tk.Tk,
    HomePageMixin,
    TableHelpersMixin,
    MaterialsPageMixin,
    RecipesPageMixin,
    ProductsPageMixin,
    SettingsPageMixin,
):
    def __init__(self):
        super().__init__()
        self.title('Nexo')
        
        wa = get_work_area()
        if wa:
            left, top, right, bottom = wa
            sw = right - left
            sh = bottom - top
        else:
            sw = self.winfo_screenwidth()
            sh = self.winfo_screenheight()
            left, top = 0, 0
            
        w = min(1280, int(sw * 0.95))
        h = min(800, int(sh * 0.85))
        x = left + (sw - w) // 2
        y = top + (sh - h) // 2
        
        self.geometry(f'{w}x{h}+{x}+{y}')
        self.minsize(1000, 600)
        self._set_icon()
        self.style = ttk.Style(self)
        try:
            self.style.theme_use('clam')
        except Exception:
            pass
        self._create_checkbox_images()
        self._build_styles()
        
        def load_hidden(key, default=['code']):
            val = get_setting(key)
            if isinstance(val, str):
                try:
                    import ast
                    val = ast.literal_eval(val)
                except: pass
            if isinstance(val, str): return [val] if val else default
            elif isinstance(val, list): return val
            return default
            
        self._rec_hidden_cols = load_hidden('rec_hidden_cols')
        self._prod_hidden_cols = load_hidden('prod_hidden_cols')
        
        # O status do banco é usado pela página Configurações durante a
        # construção do shell; ele precisa existir antes dos builders das páginas.
        self.status = tk.StringVar(value='')
        self._build_shell()
        self._bind_combobox_full_click()
        self._apply_theme()
        self.refresh_all()

    def _set_icon(self):
        try:
            if ICON_ICO.exists():
                self.iconbitmap(str(ICON_ICO))
            if ICON_PNG.exists():
                self.icon_img = tk.PhotoImage(file=str(ICON_PNG))
                self.iconphoto(True, self.icon_img)
        except Exception:
            pass

    def _create_checkbox_images(self):
        from PIL import Image, ImageDraw, ImageTk
        def make_chk(checked):
            img = Image.new('RGBA', (128, 128), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            # Fundo branco e borda
            if checked:
                draw.rounded_rectangle([16,16, 112,112], radius=24, fill='#FFFFFF', outline='#F28C28', width=12)
                # Tique delicado e perfeito dentro da caixa
                # Linha 1: Desce da esquerda para o meio
                draw.line([36,64, 56,84], fill='#F28C28', width=14)
                # Linha 2: Sobe do meio para a direita
                draw.line([56,84, 96,44], fill='#F28C28', width=14)
            else:
                draw.rounded_rectangle([16,16, 112,112], radius=24, fill='#FFFFFF', outline='#C0C9D8', width=12)
            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))
        
        self._img_chk_off = make_chk(False)
        self._img_chk_on = make_chk(True)
        
        import math
        def make_gear(color):
            img = Image.new('RGBA', (128, 128), (0,0,0,0))
            draw = ImageDraw.Draw(img)
            gcx, gcy = 64, 64
            for i in range(3):
                angle = i * (math.pi / 3)
                draw.line([gcx + 48 * math.cos(angle), gcy + 48 * math.sin(angle), gcx - 48 * math.cos(angle), gcy - 48 * math.sin(angle)], fill=color, width=22)
            draw.ellipse([gcx-36, gcy-36, gcx+36, gcy+36], fill=color)
            draw.ellipse([gcx-14, gcy-14, gcx+14, gcy+14], fill='#EEF4FB')
            return ImageTk.PhotoImage(img.resize((16, 16), Image.Resampling.LANCZOS))
        self._img_gear = make_gear('#60769D')

    def _build_styles(self):
        # Estilos base; a paleta completa é aplicada em _build_shell/_apply_theme.
        self.style.configure('TButton', padding=(12, 8), font=('Segoe UI', 10, 'bold'))
        self.style.configure('Treeview', rowheight=32, font=('Segoe UI', 9))
        self.style.configure('TLabelframe', padding=10)
        self.style.configure('Header.TLabel', font=('Segoe UI', 19, 'bold'))
        self.style.configure('SubHeader.TLabel', font=('Segoe UI', 10))
        self.style.configure('Card.TLabelframe', padding=14)

    def _build_shell(self):
        theme = get_setting('theme','light')
        dark = theme == 'dark'
        if dark:
            self.colors = {
                'bg':'#081226', 'bg_alt':'#0B1730', 'panel':'#111F3B', 'panel_alt':'#142544',
                'text':'#F4F7FF', 'muted':'#93A4C6', 'accent':'#F28C28', 'accent_dark':'#BA5200',
                'accent_soft':'#5A3518', 'line':'#24385E', 'field':'#0E1B35',
                'blue':'#2F72FF', 'cyan':'#18C39B', 'green':'#22C79A',
                'orange':'#F5A524', 'pink':'#9C5CFF', 'red':'#FF5E74',
                'sidebar':'#F28C28', 'sidebar_soft':'#C85A08', 'cream':'#FFF7EA'
            }
        else:
            self.colors = {
                'bg':'#F4F7FC', 'bg_alt':'#EEF3FA', 'panel':'#FFFFFF', 'panel_alt':'#F8FAFD',
                'text':'#18223A', 'muted':'#687796', 'accent':'#F28C28', 'accent_dark':'#BA5200',
                'accent_soft':'#FFF0D8', 'line':'#DDE5F2', 'field':'#FFFFFF',
                'blue':'#2F72FF', 'cyan':'#18A98A', 'green':'#1FAE88',
                'orange':'#F5A524', 'pink':'#9C5CFF', 'red':'#D94B3D',
                'sidebar':'#17181C', 'sidebar_soft':'#101116', 'cream':'#FFF7EA'
            }
        bg=self.colors['bg']; panel=self.colors['panel']; fg=self.colors['text']; muted=self.colors['muted']
        self.configure(bg=bg)
        self.style.configure('TFrame', background=bg)
        self.style.configure('TLabel', background=bg, foreground=fg, font=('Segoe UI',10))
        self.style.configure('Title.TLabel', background=bg, foreground=fg, font=('Segoe UI',22,'bold'))
        self.style.configure('Sub.TLabel', background=bg, foreground=muted, font=('Segoe UI',10))
        btn_bg='#172746' if dark else '#EEF2F7'; btn_fg='#DDE6FF' if dark else '#25324A'; btn_active='#20375F' if dark else '#E2E8F0'
        self.style.configure('TButton', background=btn_bg, foreground=btn_fg, padding=(12,8), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.map('TButton', background=[('active',btn_active),('pressed','#2A3F6A' if dark else '#D7DEE9')], foreground=[('disabled','#66789C'),('active','#FFFFFF' if dark else '#18223A')])
        self.style.configure('Primary.TButton', background=self.colors['accent'], foreground='#FFFFFF', padding=(15,9), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.configure('Soft.TButton', background='#EFF4FB', foreground='#1D3557', padding=(13,9), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.configure('Toolbar.TButton', background='#EFF4FB', foreground='#1D3557', padding=(13,9), font=('Segoe UI',10,'bold'), relief='flat', borderwidth=0)
        self.style.map('Primary.TButton', background=[('active',self.colors['accent_dark']),('pressed','#C75F08')], foreground=[('active','#FFFFFF')])
        self.style.configure('ActionEdit.TButton', background=btn_bg, foreground=self.colors['accent'], relief='flat', padding=(5,4), font=('Segoe UI Emoji',11,'bold'))
        self.style.configure('ActionDelete.TButton', background=btn_bg, foreground=self.colors['red'], relief='flat', padding=(5,4), font=('Segoe UI Emoji',11,'bold'))
        self.style.configure('Treeview', rowheight=38, font=('Segoe UI',10), background=self.colors['field'], fieldbackground=self.colors['field'], foreground=fg, borderwidth=0, relief='flat')
        self.style.layout('Treeview', [('Treeview.treearea', {'sticky': 'nswe'})])
        self.style.configure('Treeview.Heading', font=('Segoe UI',9,'bold'), background=(self.colors['bg_alt'] if not dark else '#142544'), foreground=(self.colors['text'] if not dark else '#AFC0E2'), relief='flat', borderwidth=0)
        self.style.map('Treeview', background=[('selected',self.colors['accent_soft'])], foreground=[('selected',fg)])
        self.style.configure('TEntry', padding=7, fieldbackground=self.colors['field'], foreground=fg, insertcolor=fg, borderwidth=0, relief='flat')
        self.style.configure('Field.TEntry', padding=4, fieldbackground=self.colors['field'], foreground=fg, insertcolor=fg, borderwidth=0, relief='flat')
        self.style.configure('TCombobox', padding=6, fieldbackground=self.colors['field'], foreground=fg, arrowcolor=('#8EA0BC' if dark else '#6A7892'))
        self.style.map('TCombobox', fieldbackground=[('readonly',self.colors['field'])], foreground=[('readonly',fg)], selectbackground=[('readonly',self.colors['field'])], selectforeground=[('readonly',fg)])
        self.style.configure('TLabelframe', background=panel, foreground=fg, borderwidth=1, relief='solid', padding=10)
        self.style.configure('TLabelframe.Label', background=panel, foreground=fg, font=('Segoe UI',10,'bold'))
        self.style.configure('TCheckbutton', background=bg, foreground=fg)
        self.style.configure('Vertical.TScrollbar', background=btn_bg, troughcolor=bg, bordercolor=bg, arrowcolor=('#91A5CC' if dark else '#7B879A'))

        root=tk.Frame(self, bg=bg); root.pack(fill='both', expand=True); self._root_frame=root

        # Sidebar reconstruída a partir da referência: marca fora da cápsula,
        # home superior sem tile e botões com ícones extraídos da própria referência.
        self.sidebar_nav = ReferenceSidebar(root, command=self.show_page, app_bg=bg, dark_theme=dark)
        self.sidebar_nav.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self._place_nexo_brand(root, dark)

        main=tk.Frame(root,bg=bg); main.place(x=150,y=0,relwidth=1.0,width=-150,relheight=1.0); self._content=main

        # Cabeçalho limpo, sem faixa laranja.
        head=tk.Frame(main,bg=bg); head.pack(fill='x',padx=18,pady=(32,14)); self._header=head
        self.header_accent=tk.Frame(head,bg=bg,height=1,width=1); self.header_accent.pack_forget()
        self.header_identity=tk.Frame(head,bg=bg); self.header_identity.pack(anchor='w')
        self.header_logo=tk.Label(self.header_identity,text='',bg=bg,bd=0)
        self.header_title=tk.Label(self.header_identity,text='Início',bg=bg,fg=fg,font=('Segoe UI',24,'bold'))
        self.header_title.pack(side='left')
        self.header_subtitle=tk.Label(head,text='Visão geral do seu negócio',bg=bg,fg=muted,font=('Segoe UI',10))
        self.header_subtitle.pack(anchor='w',pady=(2,0))
        self.company_label=tk.Label(head,text='',bg=bg,fg=muted,font=('Segoe UI',9))

        body=tk.Frame(main,bg=bg); body.pack(fill='both',expand=True); self._body=body
        self.toast_frame=tk.Frame(body,bg='#12372E',highlightthickness=0)
        self.toast_label=tk.Label(self.toast_frame,text='',bg='#12372E',fg='#61E3B9',font=('Segoe UI',9,'bold'),anchor='w',padx=12,pady=7); self.toast_label.pack(fill='x')
        self._checked_rows={}; self._action_buttons={}; self._pages={}
        pages=[('Geral',self.general),('Cadastro',self.cadastro),('Receitas',self.recipes_page),('Produtos',self.products_page),('Configurações',self.settings_page)]
        for name,builder in pages:
            f=tk.Frame(body,bg=bg); self._pages[name]=f; builder(f)
        self.show_page('Geral')

        footer=tk.Frame(main,bg=bg,height=26); footer.pack(fill='x',padx=24,pady=(0,7)); footer.pack_propagate(False)
        self.status_label=tk.Label(footer,textvariable=self.status,bg=bg,fg='#60769D',font=('Segoe UI',8),anchor='w'); self.status_label.pack(side='left',fill='y')
        self.footer_brand=tk.Label(footer,text='Nexo · Gestão de Custos e Precificação · v1.0.0   ',bg=bg,fg='#60769D',font=('Segoe UI',8),anchor='e'); self.footer_brand.pack(side='right',fill='y', padx=(0, 10))
        self._update_db_status(); bind_text_capitalization(self)

    def _place_nexo_brand(self, root, dark):
        try:
            from PIL import Image, ImageTk
            source=UI_ASSETS / ('nexo_logo_dark_clean.png' if dark else 'nexo_logo_light_clean.png')
            img=Image.open(source).convert('RGBA')
            
            target_w,target_h=135,105
            scale=min(target_w/img.width,target_h/img.height)
            img=img.resize((max(1,int(img.width*scale)),max(1,int(img.height*scale))),Image.Resampling.LANCZOS)
            self._nexo_brand_img=ImageTk.PhotoImage(img)
            self.nexo_brand_label=tk.Label(root,image=self._nexo_brand_img,bg=self.colors['bg'],bd=0,highlightthickness=0)
            self.nexo_brand_label.place(x=10,y=26,width=135,height=105)
        except Exception:
            self.nexo_brand_label=None

    def _update_db_status(self):
        try:
            with db() as c:
                c.execute('SELECT 1').fetchone()
            self.status.set(f'Banco de dados: Conectado ✓  ·  {paths.get_db_path().name}   ')
        except Exception:
            self.status.set(f'Banco de dados: Desconectado ✕  ·  {paths.get_db_path().name}   ')

    def show_page(self,key):
        if getattr(self,'current_page',None) == key:
            return
        for f in self._pages.values(): f.pack_forget()
        self._pages[key].pack(fill='both',expand=True,padx=(0, 24),pady=(0,8))
        self.current_page=key
        titles={
            'Geral':('Início','Visão geral do seu negócio   '),
            'Cadastro':('Cadastro','Gerencie insumos, compras e fornecedores   '),
            'Receitas':('Receitas','Monte e acompanhe o custo das receitas base   '),
            'Produtos':('Produtos','Custos, composição e precificação dos produtos   '),
            'Configurações':('Configurações','Preferências, dados e parâmetros do Nexo   '),
        }
        title,subtitle=titles[key]
        self.header_title.config(text=title)
        self.header_subtitle.config(text=subtitle)
        self.sidebar_nav.set_active(key)

    def refresh_all(self):
        self.refresh_general()
        self.refresh_materials()
        self.refresh_recipes()
        self.refresh_products()
        self.refresh_settings()

    def notify(self, message):
        self.toast_label.config(text=message)
        self.toast_frame.place(relx=0.5, y=30, anchor='n')
        self.toast_frame.lift()
        if hasattr(self, '_toast_after'):
            self.after_cancel(self._toast_after)
        self._toast_after = self.after(3000, self.toast_frame.place_forget)


    def apply_theme_from_settings(self):
        v=self.settings_vars['theme'].get()
        set_setting('theme', {'Claro':'light','Escuro':'dark','Sistema':'system'}.get(v,'light'));self._apply_theme()
        for pg, builder in (('Geral', self.general), ('Configurações', self.settings_page)):
            if pg in getattr(self, '_pages', {}):
                f = self._pages[pg]
                f.configure(bg=self.colors['bg'])
                for w in f.winfo_children(): w.destroy()
                builder(f)
        self.refresh_general()

    def _bind_combobox_full_click(self):
        def open_combo(event):
            w=event.widget
            try:
                if isinstance(w,ttk.Combobox) and str(w.cget('state'))!='disabled':
                    w.focus_set()
                    w.tk.call('ttk::combobox::Post', w._w)
                    return 'break'
            except Exception:
                pass
        self.bind_class('TCombobox','<Button-1>',open_combo,add='+')

    def _apply_theme(self):
        # O tema escuro é o visual principal do Nexo; o modo claro continua disponível
        # para quem preferir, mas a instalação entregue abre no Nexo Dark.
        theme=get_setting('theme','light')
        dark=theme=='dark'
        self._dark=dark
        if dark:
            bg='#081226'; fg='#F4F7FF'; panel='#111F3B'; panel_alt='#142544'; muted='#93A4C6'; line='#24385E'; field='#0E1B35'
            accent_soft='#5A3518'; cream='#FFF7EA'
        else:
            bg='#F4F7FC'; fg='#18223A'; panel='#FFFFFF'; panel_alt='#F8FAFD'; muted='#687796'; line='#DDE5F2'; field='#FFFFFF'
            accent_soft='#FFF0D8'; cream='#FFF7EA'
        self.colors.update(bg=bg,text=fg,panel=panel,panel_alt=panel_alt,muted=muted,line=line,field=field,accent_soft=accent_soft,cream=cream)
        self.configure(bg=bg)
        self.style.configure('TFrame',background=bg)
        self.style.configure('TLabel',background=bg,foreground=fg)
        self.style.configure('TLabelframe',background=panel,foreground=fg,borderwidth=1,relief='solid')
        self.style.configure('TLabelframe.Label',background=panel,foreground=fg)
        self.style.configure('Treeview',background=field,fieldbackground=field,foreground=fg,borderwidth=0,relief='flat')
        self.style.configure('Treeview.Heading',background=('#142544' if dark else '#E8EEF8'),foreground=('#AFC0E2' if dark else '#3A4967'))
        self.style.map('Treeview',background=[('selected',accent_soft)],foreground=[('selected',fg)])
        self.style.configure('TEntry',fieldbackground=field,foreground=fg,borderwidth=0,relief='flat')
        self.style.configure('Field.TEntry',fieldbackground=field,foreground=fg,borderwidth=0,relief='flat',padding=4)
        self.style.configure('TCombobox',fieldbackground=field,foreground=fg)
        self.style.configure('TButton',background=('#172746' if dark else '#EEF2F7'),foreground=('#DDE6FF' if dark else '#25324A'),padding=(12,8),font=('Segoe UI',10,'bold'),relief='flat',borderwidth=0)
        self.style.map('TButton',background=[('active','#20375F' if dark else '#E2E8F0'),('pressed','#2A3F6A' if dark else '#D7DEE9')],foreground=[('active','#FFFFFF' if dark else '#18223A')])
        self.style.map('TCombobox',fieldbackground=[('readonly',field)],foreground=[('readonly',fg)])
        self.style.configure('TCheckbutton',background=bg,foreground=fg)
        self.style.configure('Primary.TButton',background=self.colors['accent'],foreground='#FFFFFF')
        self.style.configure('Soft.TButton',background=('#172746' if dark else '#EFF4FB'),foreground=('#DDE6FF' if dark else '#1D3557'),padding=(13,9),font=('Segoe UI',10,'bold'),relief='flat',borderwidth=0)
        self.style.map('Primary.TButton',background=[('active',self.colors['accent_dark'])],foreground=[('active','#FFFFFF')])
        for attr in ('_root_frame','_content','_body'):
            w=getattr(self,attr,None)
            if w:
                try:w.configure(bg=bg)
                except Exception:pass
        if hasattr(self,'_header'):
            try:self._header.configure(bg=bg)
            except Exception:pass
        for attr in ('header_identity','header_logo','header_title','header_subtitle','company_label'):
            w=getattr(self,attr,None)
            if w:
                try:w.configure(bg=bg)
                except Exception:pass
                try:w.configure(fg=fg if attr not in ('header_subtitle','company_label') else muted)
                except Exception:pass
        for attr in ('status_label','footer_brand'):
            w=getattr(self,attr,None)
            if w:
                try:w.configure(bg=bg,fg=muted)
                except Exception:pass
        if hasattr(self,'sidebar_nav'):
            self.sidebar_nav.set_theme(dark,bg)
        if hasattr(self,'nexo_brand_label') and self.nexo_brand_label:
            try:
                from PIL import Image, ImageTk
                source=UI_ASSETS / ('nexo_logo_dark_clean.png' if dark else 'nexo_logo_light_clean.png')
                self._nexo_brand_img=ImageTk.PhotoImage(Image.open(source).convert('RGBA'))
                self.nexo_brand_label.configure(image=self._nexo_brand_img,bg=bg)
            except Exception: pass
        if hasattr(self,'purchase_chart'):
            self.after_idle(self.refresh_general)


