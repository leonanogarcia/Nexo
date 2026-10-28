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
from ..components import (
    _field_palette, rounded_entry, numeric_entry, masked_money_entry,
    safe_error, bind_text_capitalization, FlatEmojiButton,
    Modal, RoundedPanel, PillScrollbar, VerticalPillScrollbar,
    RoundedActionButton, RoundedEntry, SidebarIcon, NavItem,
    ReferenceSidebar, RoundedDropdown, CustomHistoryModal, ListDialog,
    get_work_area,
)

class HomePageMixin:
    def general(self, f):
        # Dashboard principal inspirado diretamente no layout de referência em formato cápsula.
        bg=self.colors['bg']; panel=self.colors['panel']; panel_alt=self.colors.get('panel_alt', '#142544' if getattr(self,'_dark',False) else '#F8FAFD')
        dark=getattr(self, '_dark', get_setting('theme','light')=='dark')
        canvas=tk.Canvas(f, bg=bg, highlightthickness=0, bd=0)
        body=tk.Frame(canvas, bg=bg)
        body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        win=canvas.create_window((0,0), window=body, anchor='nw')
        canvas.pack(side='left',fill='both',expand=True)
        VerticalPillScrollbar(f, canvas)
        canvas.bind('<Configure>', lambda e: canvas.itemconfigure(win,width=e.width))
        self.general_canvas=canvas
        canvas.bind_all('<MouseWheel>', self._general_mousewheel, add='+')
        canvas.bind_all('<Button-4>', self._general_mousewheel, add='+')
        canvas.bind_all('<Button-5>', self._general_mousewheel, add='+')

        cards=tk.Frame(body,bg=bg); cards.pack(fill='x',pady=(0,14))
        self.general_cards_widgets=[]
        card_defs=[
            ('Produtos','cadastrados','Produtos'),
            ('Receitas base','cadastradas','Receitas'),
            ('Insumos','cadastrados','Cadastro'),
        ]
        for i,(label,suffix,target_page) in enumerate(card_defs):
            card=RoundedPanel(cards,fill=panel,border=self.colors['line'],radius=20,height=90,bg=bg)
            card.pack(side='left',fill='both',expand=True,padx=(0 if i==0 else 6,0 if i==len(card_defs)-1 else 6)); card.pack_propagate(False)
            lbl_t=tk.Label(card,text=label,bg=panel,fg=self.colors['text'],font=('Segoe UI',10,'bold'),anchor='w')
            lbl_t.place(x=20,y=18,relwidth=.78)
            value=tk.Label(card,text='0',bg=panel,fg=self.colors['text'],font=('Segoe UI',20,'bold'),anchor='w')
            value.place(x=20,y=43,width=64,height=30)
            lbl_s=tk.Label(card,text=suffix,bg=panel,fg=self.colors['muted'],font=('Segoe UI',9),anchor='w')
            lbl_s.place(x=76,y=51)
            lbl_c=tk.Label(card,text='›',bg=panel,fg='#7790BE',font=('Segoe UI',20),anchor='center')
            lbl_c.place(relx=.93,rely=.5,anchor='center')
            def _go(_e=None, pg=target_page):
                self.show_page(pg)
                if hasattr(self, 'sidebar_nav'):
                    self.sidebar_nav.set_active(pg)
            for w_el in (card, card._canvas, lbl_t, value, lbl_s, lbl_c):
                w_el.configure(cursor='hand2')
                w_el.bind('<Button-1>', _go)
            self.general_cards_widgets.append(value)

        row=tk.Frame(body,bg=bg); row.pack(fill='x',pady=(0,14))
        chart_box=RoundedPanel(row,fill=panel,border=self.colors['line'],radius=20,height=272,bg=bg)
        chart_box.pack(side='left',fill='both',expand=True,padx=(0,7)); chart_box.pack_propagate(False)
        chart_head=tk.Frame(chart_box,bg=panel); chart_head.pack(fill='x',padx=18,pady=(14,0))
        tk.Label(chart_head,text='Custo dos Produtos',bg=panel,fg=self.colors['text'],font=('Segoe UI',12,'bold')).pack(side='left')
        period_pill=RoundedPanel(chart_head,fill=panel_alt,border=self.colors['line'],radius=14,width=124,height=28,bg=panel)
        period_pill.pack(side='right'); period_pill.pack_propagate(False)
        tk.Label(period_pill,text='Últimos 30 dias ⌄',bg=panel_alt,fg=self.colors['muted'],font=('Segoe UI',8,'bold')).pack(expand=True)
        self.purchase_chart=tk.Canvas(chart_box,height=210,bg=panel,highlightthickness=0); self.purchase_chart.pack(fill='both',expand=True,padx=10,pady=(2,8))

        stat=RoundedPanel(row,fill=panel,border=self.colors['line'],radius=20,width=294,height=272,bg=bg)
        stat.pack(side='right',fill='y',padx=(7,0)); stat.pack_propagate(False)
        inner=RoundedPanel(stat,fill=panel_alt,border=self.colors['line'],radius=18,bg=panel)
        inner.pack(fill='both',expand=True,padx=18,pady=36)
        tk.Label(inner,text='Custo médio dos produtos',bg=panel_alt,fg=self.colors['muted'],font=('Segoe UI',9,'bold'),anchor='w').pack(fill='x',padx=16,pady=(18,8))
        self.general_avg_cost=tk.Label(inner,text='R$ 0,00',bg=panel_alt,fg=self.colors['text'],font=('Segoe UI',24,'bold'),anchor='w')
        self.general_avg_cost.pack(fill='x',padx=16)
        pill_bg = '#123B39' if dark else '#E6F9F5'
        pill_fg = '#56D4B4' if dark else '#0F9D7A'
        status_pill_wrap=RoundedPanel(inner,fill=pill_bg,border='',radius=14,width=142,height=28,bg=panel_alt)
        status_pill_wrap.pack(anchor='w',padx=16,pady=(10,4)); status_pill_wrap.pack_propagate(False)
        self.general_status_pill=tk.Label(status_pill_wrap,text='calculado agora',bg=pill_bg,fg=pill_fg,font=('Segoe UI',9,'bold'))
        self.general_status_pill.pack(expand=True)
        tk.Label(inner,text='com base nos custos cadastrados',bg=panel_alt,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',padx=16,pady=(2,14))

        lower=tk.Frame(body,bg=bg); lower.pack(fill='x',pady=(0,14))
        purchases=RoundedPanel(lower,fill=panel,border=self.colors['line'],radius=20,height=224,bg=bg)
        purchases.pack(side='left',fill='both',expand=True,padx=(0,7)); purchases.pack_propagate(False)
        tk.Label(purchases,text='Compras',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(fill='x',padx=18,pady=(14,0))
        tk.Label(purchases,text='últimos 30 dias',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',padx=18,pady=(1,7))
        self.general_purchase_lines=tk.Frame(purchases,bg=panel); self.general_purchase_lines.pack(fill='both',expand=True,padx=18,pady=(0,10))

        variation=RoundedPanel(lower,fill=panel,border=self.colors['line'],radius=20,height=224,bg=bg)
        variation.pack(side='right',fill='both',expand=True,padx=(7,0)); variation.pack_propagate(False)
        tk.Label(variation,text='Variação de preços',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(fill='x',padx=18,pady=(14,0))
        tk.Label(variation,text='histórico por insumo',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',padx=18,pady=(1,7))
        self.general_variation_lines=tk.Frame(variation,bg=panel); self.general_variation_lines.pack(fill='both',expand=True,padx=18,pady=(0,10))

        recent=RoundedPanel(body,fill=panel,border=self.colors['line'],radius=20,height=220,bg=bg)
        recent.pack(fill='x',pady=(0,14)); recent.pack_propagate(False)
        top=tk.Frame(recent,bg=panel); top.pack(fill='x',padx=18,pady=(13,6))
        tk.Label(top,text='Últimas movimentações',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(side='left')
        tk.Label(top,text='Ver todas  →',bg=panel,fg='#F28C28',font=('Segoe UI',9,'bold'),anchor='e').pack(side='right')
        header_pill=RoundedPanel(recent,fill=panel_alt,border='',radius=14,height=28,bg=panel)
        header_pill.pack(fill='x',padx=18,pady=(0,4)); header_pill.pack_propagate(False)
        header=tk.Frame(header_pill,bg=panel_alt); header.pack(fill='both',expand=True,padx=12)
        for txt,w in [('Data',22),('Descrição',52),('Tipo',16),('Valor',16)]:
            tk.Label(header,text=txt,bg=panel_alt,fg=self.colors['muted'],font=('Segoe UI',8,'bold'),anchor='w',width=w).pack(side='left',fill='x',expand=(txt=='Descrição'))
        self.general_recent=tk.Frame(recent,bg=panel); self.general_recent.pack(fill='both',expand=True,padx=18,pady=(0,10))

        # BI visual em gráficos de pizza/rosca no Início + botão para abrir Modal de BI detalhado
        bi_row=tk.Frame(body,bg=bg); bi_row.pack(fill='x',pady=(0,20))

        bi_left=RoundedPanel(bi_row,fill=panel,border=self.colors['line'],radius=20,height=252,bg=bg)
        bi_left.pack(side='left',fill='both',expand=True,padx=(0,7)); bi_left.pack_propagate(False)
        bi_l_head=tk.Frame(bi_left,bg=panel); bi_l_head.pack(fill='x',padx=18,pady=(14,2))
        bi_l_titles=tk.Frame(bi_l_head,bg=panel); bi_l_titles.pack(side='left',fill='x',expand=True)
        tk.Label(bi_l_titles,text='Histórico mensal de compras',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(anchor='w')
        tk.Label(bi_l_titles,text='participação por insumo',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(anchor='w')
        RoundedActionButton(bi_l_head,'Ver detalhes',lambda:self.open_bi_modal('insumo'),width=120,height=32,fill='#F28C28',hover='#BA5200',fg='#FFFFFF',bg=panel).pack(side='right')
        self.purchase_pie_canvas=tk.Canvas(bi_left,height=175,bg=panel,highlightthickness=0,bd=0)
        self.purchase_pie_canvas.pack(fill='both',expand=True,padx=14,pady=(2,10))
        self.purchase_pie_canvas.bind('<Configure>', lambda e: self.after_idle(self._redraw_bi_pies))

        bi_right=RoundedPanel(bi_row,fill=panel,border=self.colors['line'],radius=20,height=252,bg=bg)
        bi_right.pack(side='right',fill='both',expand=True,padx=(7,0)); bi_right.pack_propagate(False)
        bi_r_head=tk.Frame(bi_right,bg=panel); bi_r_head.pack(fill='x',padx=18,pady=(14,2))
        bi_r_titles=tk.Frame(bi_r_head,bg=panel); bi_r_titles.pack(side='left',fill='x',expand=True)
        tk.Label(bi_r_titles,text='Evolução de custos',bg=panel,fg=self.colors['text'],font=('Segoe UI',11,'bold'),anchor='w').pack(anchor='w')
        tk.Label(bi_r_titles,text='comparativo de receitas e produtos',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(anchor='w')
        RoundedActionButton(bi_r_head,'Ver detalhes',lambda:self.open_bi_modal('custos'),width=120,height=32,fill='#F28C28',hover='#BA5200',fg='#FFFFFF',bg=panel).pack(side='right')
        self.cost_pie_canvas=tk.Canvas(bi_right,height=175,bg=panel,highlightthickness=0,bd=0)
        self.cost_pie_canvas.pack(fill='both',expand=True,padx=14,pady=(2,10))
        self.cost_pie_canvas.bind('<Configure>', lambda e: self.after_idle(self._redraw_bi_pies))

    def _general_mousewheel(self, event):
        try:
            if event.widget.winfo_toplevel() is not self:
                return
        except Exception:
            pass
        delta = -int(event.delta/120) if getattr(event,'delta',0) else (-1 if getattr(event,'num',0)==4 else 1)
        page = getattr(self, 'current_page', None)
        if page == 'Geral' and hasattr(self, 'general_canvas'):
            c = self.general_canvas
            if c and c.winfo_exists():
                first, last = c.yview()
                if (delta < 0 and first > 0.0) or (delta > 0 and last < 1.0):
                    c.yview_scroll(delta, 'units')
                return 'break'
        if page == 'Configurações':
            c = getattr(self, '_settings_canvases', {}).get(getattr(self, '_active_settings_key', None))
            if c and c.winfo_exists():
                first, last = c.yview()
                if (delta < 0 and first > 0.0) or (delta > 0 and last < 1.0):
                    c.yview_scroll(delta, 'units')
                return 'break'

    def _draw_bi_chart(self, canvas, title, series, value_label='R$'):
        canvas.delete('all')
        w=max(canvas.winfo_width(),620); h=max(int(canvas['height']),180)
        bg=self.colors['panel']; fg=self.colors['text']; muted=self.colors['muted']; grid=self.colors['line']; accent=self.colors['accent']
        canvas.configure(bg=bg)
        if not series:
            canvas.create_text(w/2,h/2,text='Ainda não há histórico suficiente para exibir este gráfico.',fill=muted,font=('Segoe UI',10))
            return
        data=series[-10:]; vals=[float(x[1] or 0) for x in data]
        mn=min(vals); mx=max(vals)
        if mx == mn:
            mx = mn + max(abs(mn)*0.2, 1)
            mn = max(0, mn - max(abs(mn)*0.2, 1))
        left,bottom,top,right=62,h-34,24,w-20
        # grade horizontal e rótulos de valor
        for i in range(5):
            y=top+(bottom-top)*i/4
            val=mx-(mx-mn)*i/4
            canvas.create_line(left,y,right,y,fill=grid,width=1)
            label=(f'R$ {val:,.2f}'.replace(',','X').replace('.',',').replace('X','.') if value_label=='R$' else f'{val:,.2f}')
            canvas.create_text(left-8,y,text=label,fill=muted,font=('Segoe UI',8),anchor='e')
        n=len(data)
        if n==1:
            xs=[(left+right)/2]
        else:
            xs=[left+i*(right-left)/(n-1) for i in range(n)]
        pts=[]
        for x,v in zip(xs,vals):
            y=bottom-(v-mn)/(mx-mn)*(bottom-top)
            pts.extend((x,y))
        # preenchimento suave sob a linha (cor sólida escura por limitação do Canvas Tk).
        if len(pts)>=4:
            poly=[left,bottom] + pts + [right,bottom]
            canvas.create_polygon(poly,fill=self.colors['accent_soft'],outline='')
            canvas.create_line(*pts,fill=accent,width=3,smooth=True,splinesteps=20)
        else:
            x,y=pts; canvas.create_line(left,y,right,y,fill=accent,width=3)
        for i,((label,v),x) in enumerate(zip(data,xs)):
            y=bottom-(v-mn)/(mx-mn)*(bottom-top)
            canvas.create_oval(x-4,y-4,x+4,y+4,fill=accent,outline='#8D85FF',width=1)
            if i==0 or i==len(data)-1 or len(data)<=6 or i%2==0:
                canvas.create_text(x,bottom+10,text=str(label),fill=muted,font=('Segoe UI',8),anchor='n')

    def refresh_general(self):
        if not hasattr(self, 'general_cards_widgets'):
            return
        panel=self.colors['panel']
        with db() as c:
            ins = c.execute('SELECT COUNT(*) n FROM materials WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0').fetchone()['n']
            recipes = c.execute('SELECT COUNT(*) n FROM base_recipes WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0').fetchone()['n']
            products = c.execute('SELECT COUNT(*) n FROM products WHERE COALESCE(active,1)=1 AND COALESCE(archived,0)=0').fetchone()['n']
        costs=[]; prices=[]
        for r in list_names('products'):
            try: costs.append(product_unit_cost(r['id']))
            except Exception: pass
            with db() as c:
                pr=c.execute('SELECT sale_price FROM products WHERE id=?',(r['id'],)).fetchone()
                if pr and pr['sale_price'] is not None: prices.append(pr['sale_price'])
        avg_cost = sum(costs)/len(costs) if costs else 0
        labels = [str(products), str(recipes), str(ins)]
        for w, value in zip(self.general_cards_widgets, labels):
            w.config(text=value)
        if hasattr(self,'general_avg_cost'): self.general_avg_cost.config(text=fmt(avg_cost))

        if hasattr(self,'general_purchase_lines'):
            for w in self.general_purchase_lines.winfo_children(): w.destroy()
            with db() as c:
                rows=c.execute('''SELECT COALESCE(m.category,'Outros') category, SUM(pu.value) total
                                  FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                  WHERE date(pu.purchase_date) >= date('now','-30 day')
                                  GROUP BY m.category ORDER BY total DESC''').fetchall()
                if not rows:
                    rows=c.execute('''SELECT COALESCE(m.category,'Outros') category, SUM(pu.value) total
                                      FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                      GROUP BY m.category ORDER BY total DESC LIMIT 4''').fetchall()
            total=sum(float(r['total'] or 0) for r in rows) or 1
            palette=[('#24C6A3','Comestível'),('#7B5CFF','Não comestível'),('#2F72FF','Doação'),('#F5A524','Outros')]
            for idx,r in enumerate(rows[:4]):
                row=tk.Frame(self.general_purchase_lines,bg=panel); row.pack(fill='x',pady=2)
                dot,color_name=palette[idx%len(palette)]
                category=str(r['category'] or '')
                name=category or color_name
                tk.Label(row,text='●',bg=panel,fg=dot,font=('Segoe UI',9)).pack(side='left')
                tk.Label(row,text=name,bg=panel,fg=self.colors['text'],font=('Segoe UI',8),anchor='w').pack(side='left',fill='x',expand=True,padx=(6,4))
                val=float(r['total'] or 0); pct=val/total*100
                tk.Label(row,text=fmt(val),bg=panel,fg=self.colors['text'],font=('Segoe UI',8,'bold'),anchor='e').pack(side='left',padx=5)
                tk.Label(row,text=f'{pct:.0f}%',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),width=5,anchor='e').pack(side='right')
            if not rows:
                tk.Label(self.general_purchase_lines,text='Nenhuma compra registrada ainda.',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',pady=8)

        if hasattr(self,'general_variation_lines'):
            for w in self.general_variation_lines.winfo_children(): w.destroy()
            with db() as c:
                rows=c.execute('''SELECT m.name, MIN(pu.value) mn, MAX(pu.value) mx
                                  FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                  GROUP BY m.id HAVING COUNT(pu.id) > 1
                                  ORDER BY CASE WHEN MIN(pu.value)>0 THEN (MAX(pu.value)-MIN(pu.value))/MIN(pu.value) ELSE 0 END DESC LIMIT 5''').fetchall()
            for r in rows:
                mn=float(r['mn'] or 0); mx=float(r['mx'] or 0)
                pct=((mx-mn)/mn*100) if mn>0 else 0
                row=tk.Frame(self.general_variation_lines,bg=panel); row.pack(fill='x',pady=4)
                tk.Label(row,text=r['name'],bg=panel,fg=self.colors['text'],font=('Segoe UI',8),anchor='w').pack(side='left',fill='x',expand=True)
                positive=pct>0.01
                txt=('↑ ' if positive else '↓ ') + f'{abs(pct):.1f}%'.replace('.',',')
                tk.Label(row,text=txt,bg=panel,fg=('#FF5E74' if positive else '#24C6A3'),font=('Segoe UI',9,'bold'),anchor='e').pack(side='right')
            if not rows:
                tk.Label(self.general_variation_lines,text='Ainda não há histórico suficiente.',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',pady=8)

        if hasattr(self,'general_recent'):
            for w in self.general_recent.winfo_children(): w.destroy()
            with db() as c:
                rows=c.execute('''SELECT pu.purchase_date date, m.name, COALESCE(pu.brand,'') brand, pu.value
                                  FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                  ORDER BY pu.purchase_date DESC, pu.id DESC LIMIT 4''').fetchall()
            if rows:
                dark=getattr(self, '_dark', get_setting('theme','light')=='dark')
                tag_bg='#123B39' if dark else '#E6F9F5'
                tag_fg='#5EE0B8' if dark else '#0F9D7A'
                for r in rows:
                    row=tk.Frame(self.general_recent,bg=panel); row.pack(fill='x',pady=2)
                    date_text=str(r['date'])
                    desc=r['name'] + (f" - {r['brand']}" if r['brand'] else '')
                    tk.Label(row,text=date_text,bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w',width=22).pack(side='left')
                    tk.Label(row,text=desc,bg=panel,fg=self.colors['text'],font=('Segoe UI',8),anchor='w').pack(side='left',fill='x',expand=True)
                    tag_pill=RoundedPanel(row,fill=tag_bg,border='',radius=11,width=76,height=22,bg=panel)
                    tag_pill.pack(side='left',padx=8); tag_pill.pack_propagate(False)
                    tk.Label(tag_pill,text='Compra',bg=tag_bg,fg=tag_fg,font=('Segoe UI',8,'bold')).pack(expand=True)
                    tk.Label(row,text=fmt(r['value']),bg=panel,fg=self.colors['text'],font=('Segoe UI',8,'bold'),anchor='e',width=15).pack(side='right')
            else:
                tk.Label(self.general_recent,text='Nenhuma movimentação registrada ainda.',bg=panel,fg=self.colors['muted'],font=('Segoe UI',8),anchor='w').pack(fill='x',pady=8)

        # Dados para os gráficos de pizza de BI e para o Modal detalhado
        with db() as c:
            pie_purch = c.execute('''SELECT m.name, SUM(pu.value) total
                                     FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                     GROUP BY m.id ORDER BY total DESC''').fetchall()
        self._bi_purchase_slices = [(r['name'], float(r['total'] or 0)) for r in pie_purch if float(r['total'] or 0) > 0]

        cost_slices = []
        for r in list_names('products'):
            try:
                v = float(product_unit_cost(r['id']) or 0)
                if v > 0: cost_slices.append((f"Prod: {r['name']}", v))
            except Exception:
                pass
        for r in list_names('base_recipes'):
            try:
                v = float(recipe_cost(r['id']) or 0)
                if v > 0: cost_slices.append((f"Rec: {r['name']}", v))
            except Exception:
                pass
        cost_slices.sort(key=lambda x: x[1], reverse=True)
        self._bi_cost_slices = cost_slices
        self._redraw_bi_pies()

        with db() as c:
            hist_series=c.execute('SELECT substr(recorded_at,1,7) mes, AVG(cost) avg_cost FROM cost_history GROUP BY mes ORDER BY mes').fetchall()
        if hist_series:
            cost_series=[(r['mes'],float(r['avg_cost'])) for r in hist_series]
        else:
            current=[]
            for r in list_names('products'):
                try:current.append(product_unit_cost(r['id']))
                except Exception:pass
            for r in list_names('base_recipes'):
                try:current.append(recipe_cost(r['id']))
                except Exception:pass
            cost_series=[(date.today().strftime('%Y-%m'),sum(current)/len(current))] if current else []
        self._draw_bi_chart(self.purchase_chart,'Custo médio por mês',cost_series)

    def _redraw_bi_pies(self):
        if hasattr(self, 'purchase_pie_canvas') and self.purchase_pie_canvas.winfo_exists():
            self._draw_pie_chart(self.purchase_pie_canvas, getattr(self, '_bi_purchase_slices', []), 'Sem compras registradas.', '_purch_pie_img')
        if hasattr(self, 'cost_pie_canvas') and self.cost_pie_canvas.winfo_exists():
            self._draw_pie_chart(self.cost_pie_canvas, getattr(self, '_bi_cost_slices', []), 'Sem custos calculados.', '_cost_pie_img')

    def _draw_pie_chart(self, canvas, slices, empty_msg, img_attr):
        canvas.delete('all')
        panel = self.colors['panel']
        fg = self.colors['text']
        muted = self.colors['muted']
        canvas.configure(bg=panel)
        w = max(canvas.winfo_width(), 340)
        h = max(canvas.winfo_height(), 165)
        if not slices:
            canvas.create_text(w/2, h/2, text=empty_msg, fill=muted, font=('Segoe UI', 9))
            return
        top_slices = list(slices[:4])
        rest = sum(v for _, v in slices[4:])
        if rest > 0:
            top_slices.append(('Outros', rest))
        total = sum(v for _, v in top_slices) or 1.0
        palette = ('#F28C28', '#2F72FF', '#18C39B', '#9C5CFF', '#FF5E74')

        pie_size = min(136, h - 16)
        cx_pie = 16 + pie_size // 2
        cy_pie = h // 2
        try:
            from PIL import Image, ImageDraw, ImageTk
            scale = 4
            S = pie_size * scale
            im = Image.new('RGB', (S, S), panel)
            d = ImageDraw.Draw(im)
            start_ang = -90.0
            for idx, (_, val) in enumerate(top_slices):
                extent = (val / total) * 360.0
                end_ang = start_ang + max(extent, 1.5)
                col = palette[idx % len(palette)]
                d.pieslice((4, 4, S - 5, S - 5), start=start_ang, end=end_ang, fill=col, outline=panel, width=scale*2)
                start_ang += extent
            hole_r = int(S * 0.28)
            d.ellipse((S//2 - hole_r, S//2 - hole_r, S//2 + hole_r, S//2 + hole_r), fill=panel)
            im = im.resize((pie_size, pie_size), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(im)
            setattr(self, img_attr, photo)
            canvas.create_image(cx_pie, cy_pie, image=photo, anchor='center')
        except Exception:
            start_ang = 90.0
            r = pie_size // 2
            for idx, (_, val) in enumerate(top_slices):
                extent = -(val / total) * 360.0
                col = palette[idx % len(palette)]
                canvas.create_arc(cx_pie - r, cy_pie - r, cx_pie + r, cy_pie + r, start=start_ang, extent=extent, fill=col, outline=panel, width=2)
                start_ang += extent

        lx = 16 + pie_size + 18
        n = len(top_slices)
        row_h = min(28, max(20, (h - 20) // max(n, 1)))
        start_y = cy_pie - (n * row_h) // 2 + row_h // 2
        for idx, (name, val) in enumerate(top_slices):
            y = start_y + idx * row_h
            col = palette[idx % len(palette)]
            pct = (val / total) * 100.0
            canvas.create_oval(lx, y - 5, lx + 10, y + 5, fill=col, outline='')
            disp_name = name if len(name) <= 22 else name[:20] + '…'
            canvas.create_text(lx + 16, y, text=disp_name, fill=fg, font=('Segoe UI', 8, 'bold'), anchor='w')
            canvas.create_text(w - 44, y, text=fmt(val), fill=fg, font=('Segoe UI', 8), anchor='e')
            canvas.create_text(w - 6, y, text=f'{pct:.0f}%', fill=muted, font=('Segoe UI', 8, 'bold'), anchor='e')

    def open_bi_modal(self, initial_tab='insumo'):
        d = Modal(self, 'BI — Histórico de Compras e Evolução de Custos', '920x560')
        bg = self.colors.get('bg', '#F4F7FC')
        fg = self.colors.get('text', '#18223A')
        muted = self.colors.get('muted', '#687796')
        dark = getattr(self, '_dark', False)
        d.configure(bg=bg)

        # Rodapé no padrão Nexo
        act_frame = tk.Frame(d, bg=bg)
        act_frame.pack(side='bottom', fill='x', padx=24, pady=(12, 20))
        RoundedActionButton(act_frame, 'Fechar', d.destroy, width=110, height=36, fill='#F28C28', hover='#BA5200', fg='#FFFFFF', bg=bg).pack(side='right', padx=(8, 0))

        # Barra superior (Título + Abas em Cápsula + Pesquisa de 32px)
        top_bar = tk.Frame(d, bg=bg)
        top_bar.pack(side='top', fill='x', padx=24, pady=(20, 12))

        tabs_frame = tk.Frame(top_bar, bg=bg)
        tabs_frame.pack(side='left')

        search_var = tk.StringVar()
        search_entry = RoundedEntry(top_bar, textvariable=search_var, width=210, height=32, placeholder='Filtrar...')
        search_entry.pack(side='right')

        # Área da Tabela no padrão Nexo (Canvas arredondado + Treeview show='tree' + VerticalPillScrollbar)
        table_frame = tk.Frame(d, bg=bg)
        table_frame.pack(fill='both', expand=True, padx=24)

        header_canvas = tk.Canvas(table_frame, height=36, bg=bg, highlightthickness=0, bd=0)
        header_canvas.pack(side='top', fill='x')

        tree_container = tk.Frame(table_frame, bg=bg)
        tree_container.pack(side='top', fill='both', expand=True)

        state = {'tab': initial_tab, 'columns': [], 'rows': [], 'sort_dirs': {}, 'tree': None, 'vsb': None}

        # Carrega os dados das 3 visões do BI
        with db() as c:
            r_ins = c.execute('''SELECT m.name, substr(pu.purchase_date,1,7) mes, MIN(pu.value) mn, MAX(pu.value) mx, AVG(pu.value) av
                                 FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                 GROUP BY m.id, mes ORDER BY mes DESC, m.name''').fetchall()
            rows_insumo = [(r['name'], r['mes'], fmt(r['mn']), fmt(r['mx']), fmt(r['av'])) for r in r_ins]

            r_br = c.execute('''SELECT m.name, COALESCE(pu.brand,'') brand, substr(pu.purchase_date,1,7) mes, MIN(pu.value) mn, MAX(pu.value) mx, AVG(pu.value) av
                                FROM purchases pu JOIN materials m ON m.id=pu.material_id
                                GROUP BY m.id, pu.brand, mes ORDER BY mes DESC, m.name, pu.brand''').fetchall()
            rows_marca = [(r['name'], r['brand'] or '—', r['mes'], fmt(r['mn']), fmt(r['mx']), fmt(r['av'])) for r in r_br]

            r_ch = c.execute('''SELECT ch.entity_type, ch.entity_id, ch.cost, substr(ch.recorded_at,1,7) mes
                                FROM cost_history ch ORDER BY ch.recorded_at DESC, ch.id DESC''').fetchall()
            rows_custos = []
            for r in r_ch:
                tbl = 'base_recipes' if r['entity_type'] == 'RECIPE_BASE' else 'products'
                nm = c.execute(f'SELECT name FROM {tbl} WHERE id=?', (r['entity_id'],)).fetchone()
                rows_custos.append(('Receita' if r['entity_type'] == 'RECIPE_BASE' else 'Produto', nm['name'] if nm else '?', r['mes'], fmt(r['cost'])))
        if not rows_custos:
            mes_now = date.today().strftime('%Y-%m')
            for r in list_names('base_recipes'):
                try: rows_custos.append(('Receita', r['name'], mes_now, fmt(recipe_cost(r['id']))))
                except Exception: pass
            for r in list_names('products'):
                try: rows_custos.append(('Produto', r['name'], mes_now, fmt(product_unit_cost(r['id']))))
                except Exception: pass

        tab_specs = {
            'insumo': (
                'Variação por Insumo',
                [('item', 'Insumo', 300), ('mes', 'Mês', 120), ('min', 'Mínimo', 140), ('max', 'Máximo', 140), ('media', 'Média', 140)],
                rows_insumo
            ),
            'marca': (
                'Variação por Marca',
                [('item', 'Insumo', 230), ('marca', 'Marca', 160), ('mes', 'Mês', 100), ('min', 'Mínimo', 120), ('max', 'Máximo', 120), ('media', 'Média', 120)],
                rows_marca
            ),
            'custos': (
                'Evolução de Custos',
                [('tipo', 'Tipo', 140), ('item', 'Receita / Produto', 360), ('mes', 'Mês', 140), ('custo', 'Custo', 180)],
                rows_custos
            ),
        }

        def draw_header(_=None):
            c = header_canvas
            c.delete('all')
            w = max(c.winfo_width(), 2)
            h = max(c.winfo_height(), 2)
            r = min(h/2, 18)
            fill = '#142544' if dark else '#EEF4FB'
            c.create_rectangle(r, 0, w-r, h, fill=fill, outline='')
            c.create_rectangle(0, r, w, h-r, fill=fill, outline='')
            c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=fill, outline=fill)
            c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90, fill=fill, outline=fill)
            c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90, fill=fill, outline=fill)
            c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90, fill=fill, outline=fill)

            cols = state['columns']
            tree = state['tree']
            if not tree or not cols:
                return
            x0 = 0
            for idx, (key, txt, width) in enumerate(cols):
                try: cw = int(tree.column(key, 'width'))
                except Exception: cw = width
                align = 'w' if key in ('item', 'marca', 'tipo') else 'center'
                anchor_x = x0 + 14 if align == 'w' else x0 + cw / 2
                arrow = ''
                if key in state['sort_dirs']:
                    arrow = ' ▼' if not state['sort_dirs'][key] else ' ▲'
                full_txt = txt + arrow if align == 'w' else arrow + txt
                tid = c.create_text(anchor_x, h/2, text=full_txt, fill='#AFC0E2' if dark else '#60769D', font=('Segoe UI', 9, 'bold'), anchor=align)
                c.create_rectangle(x0, 0, x0+cw, h, fill='', outline='', tags=(f'hdr_{key}',))
                c.tag_bind(f'hdr_{key}', '<Enter>', lambda e, t=tid: (c.itemconfig(t, fill='#BA5200'), c.config(cursor='hand2')))
                c.tag_bind(f'hdr_{key}', '<Leave>', lambda e, t=tid: (c.itemconfig(t, fill='#AFC0E2' if dark else '#60769D'), c.config(cursor='')))
                c.tag_bind(f'hdr_{key}', '<Button-1>', lambda e, k=key: sort_col(k))
                if idx < len(cols) - 1:
                    c.create_line(x0+cw, 6, x0+cw, h-6, fill=self.colors.get('line', '#E5ECF5'))
                x0 += cw

        def sort_col(col):
            tree = state['tree']
            if not tree: return
            rev = state['sort_dirs'].get(col, False)
            items = [(tree.set(k, col), k) for k in tree.get_children('')]
            try:
                items.sort(key=lambda t: float(t[0].replace('R$ ', '').replace('.', '').replace(',', '.')), reverse=not rev)
            except Exception:
                items.sort(key=lambda t: t[0].lower(), reverse=not rev)
            for idx, (_, k) in enumerate(items):
                tree.move(k, '', idx)
            state['sort_dirs'] = {col: not rev}
            draw_header()

        def populate_filtered(*_):
            tree = state['tree']
            if not tree: return
            tree.delete(*tree.get_children())
            q = search_var.get().strip().lower()
            for r in state['rows']:
                if not q or any(q in str(v).lower() for v in r):
                    tree.insert('', 'end', values=r)

        tab_pills = {}
        def switch_tab(tab_key):
            state['tab'] = tab_key
            state['sort_dirs'] = {}
            _, cols, rows = tab_specs[tab_key]
            state['columns'] = cols
            state['rows'] = rows

            for k, (pill, lbl) in tab_pills.items():
                is_act = (k == tab_key)
                p_fill = '#F28C28' if is_act else ('#172746' if dark else '#EFF4FB')
                p_fg = '#FFFFFF' if is_act else ('#DDE6FF' if dark else '#1D3557')
                pill.set_style(fill=p_fill, bg=bg)
                lbl.configure(bg=p_fill, fg=p_fg, font=('Segoe UI', 9, 'bold' if is_act else 'normal'))

            for w_child in tree_container.winfo_children():
                w_child.destroy()

            tree = ttk.Treeview(tree_container, columns=[c[0] for c in cols], show='tree')
            tree.column('#0', width=0, stretch=False)
            for k, _, w in cols:
                tree.column(k, width=w, anchor='w' if k in ('item', 'marca', 'tipo') else 'center')
            tree.pack(side='left', fill='both', expand=True)
            vsb = VerticalPillScrollbar(tree_container, tree)
            state['tree'] = tree
            state['vsb'] = vsb
            populate_filtered()
            tree.bind('<Configure>', lambda e: tree.after_idle(draw_header))
            d.after_idle(draw_header)

        for t_key, (t_label, _, _) in tab_specs.items():
            pill = RoundedPanel(tabs_frame, fill='#EFF4FB', border='', radius=16, width=165, height=32, bg=bg)
            pill.pack(side='left', padx=(0, 8)); pill.pack_propagate(False)
            lbl = tk.Label(pill, text=t_label, bg='#EFF4FB', fg='#1D3557', font=('Segoe UI', 9), cursor='hand2')
            lbl.pack(expand=True)
            tab_pills[t_key] = (pill, lbl)
            for el in (pill, pill._canvas, lbl):
                el.configure(cursor='hand2')
                el.bind('<Button-1>', lambda e, k=t_key: switch_tab(k))

        def export_csv():
            import csv
            path = filedialog.asksaveasfilename(parent=d, defaultextension='.csv', filetypes=[('CSV (Excel)', '*.csv')], title='Exportar BI')
            if not path: return
            try:
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';')
                    writer.writerow([c[1] for c in state['columns']])
                    for iid in state['tree'].get_children():
                        writer.writerow(state['tree'].item(iid)['values'])
                self.notify('Relatório de BI exportado com sucesso!')
            except Exception as ex:
                safe_error(d, 'Erro na exportação', ex)

        RoundedActionButton(act_frame, '📄 Exportar Relatório', export_csv, width=180, height=36, fill='#EAFaf1', hover='#D4E6DC', fg='#1E833F', bg=bg).pack(side='left')
        header_canvas.bind('<Configure>', draw_header)
        search_var.trace_add('write', populate_filtered)
        switch_tab(initial_tab if initial_tab in tab_specs else 'insumo')

