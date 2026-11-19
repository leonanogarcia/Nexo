import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
INSTALLER_DIR = ROOT_DIR / 'installer'
OUTPUT_DIR = ROOT_DIR / 'instaladores'


def detect_version() -> str:
    import json
    pkg_file = ROOT_DIR / 'frontend' / 'package.json'
    if pkg_file.exists():
        try:
            ver = str(json.loads(pkg_file.read_text(encoding='utf-8')).get('version') or '').strip()
            if re.match(r'^\d+\.\d+\.\d+$', ver):
                return ver
        except Exception:
            pass
    main_file = ROOT_DIR / 'main.py'
    if main_file.exists():
        m = re.search(r'v(\d+\.\d+\.\d+)', main_file.read_text(encoding='utf-8'))
        if m:
            return m.group(1)
    return '2.0.0'


def make_pyinstaller_version_info(version: str) -> str:
    parts = (version.split('.') + ['0', '0', '0', '0'])[:4]
    ver_tuple = ', '.join(str(int(x)) for x in parts)
    ver_str = '.'.join(str(int(x)) for x in parts)
    return f'''# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({ver_tuple}),
    prodvers=({ver_tuple}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        '041604B0',
        [StringStruct('CompanyName', 'Leonan Garcia'),
        StringStruct('FileDescription', 'Nexo - Gestão de Custos e Precificação'),
        StringStruct('FileVersion', '{ver_str}'),
        StringStruct('InternalName', 'Nexo'),
        StringStruct('LegalCopyright', '© 2026 Leonan Garcia. Todos os direitos reservados.'),
        StringStruct('OriginalFilename', 'Nexo.exe'),
        StringStruct('ProductName', 'Nexo'),
        StringStruct('ProductVersion', '{ver_str}')])
      ]),
    VarFileInfo([VarStruct('Translation', [1046, 1200])])
  ]
)
'''


UAC_MANIFEST_XML = '''<?xml version="1.0" encoding="utf-8"?>
<assembly manifestVersion="1.0" xmlns="urn:schemas-microsoft-com:asm.v1">
  <assemblyIdentity version="1.0.0.0" name="Nexo.Setup.app"/>
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v2">
    <security>
      <requestedPrivileges xmlns="urn:schemas-microsoft-com:asm.v3">
        <requestedExecutionLevel level="requireAdministrator" uiAccess="false" />
      </requestedPrivileges>
    </security>
  </trustInfo>
</assembly>
'''

CSHARP_UNINSTALLER_TEMPLATE = r'''
using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Reflection;
using System.Security.Principal;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Nexo - Gestão de Custos e Precificação")]
[assembly: AssemblyDescription("Desinstalador do Nexo")]
[assembly: AssemblyCompany("Leonan Garcia")]
[assembly: AssemblyProduct("Nexo")]
[assembly: AssemblyCopyright("© 2026 Leonan Garcia. Todos os direitos reservados.")]
[assembly: AssemblyVersion("__VERSION__.0")]
[assembly: AssemblyFileVersion("__VERSION__.0")]

namespace NexoUninstall
{
    public static class NexoDraw
    {
        public static GraphicsPath RoundedRect(Rectangle bounds, int radius)
        {
            GraphicsPath path = new GraphicsPath();
            int d = Math.Min(radius, Math.Min(bounds.Width, bounds.Height));
            if (d <= 0) {
                path.AddRectangle(bounds);
                return path;
            }
            Rectangle arc = new Rectangle(bounds.Location, new Size(d, d));
            path.AddArc(arc, 180, 90);
            arc.X = bounds.Right - d;
            path.AddArc(arc, 270, 90);
            arc.Y = bounds.Bottom - d;
            path.AddArc(arc, 0, 90);
            arc.X = bounds.Left;
            path.AddArc(arc, 90, 90);
            path.CloseFigure();
            return path;
        }
    }

    public class PillButton : Control
    {
        public Color BackColorNormal { get; set; }
        public Color BackColorHover { get; set; }
        public Color BorderColor { get; set; }
        private bool isHovered = false;

        public PillButton()
        {
            this.SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            this.BackColor = Color.Transparent;
            this.Cursor = Cursors.Hand;
            this.BackColorNormal = Color.FromArgb(242, 140, 40);
            this.BackColorHover = Color.FromArgb(223, 123, 23);
            this.BorderColor = Color.Transparent;
        }

        protected override void OnMouseEnter(EventArgs e) { isHovered = true; Invalidate(); base.OnMouseEnter(e); }
        protected override void OnMouseLeave(EventArgs e) { isHovered = false; Invalidate(); base.OnMouseLeave(e); }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            Rectangle rect = new Rectangle(0, 0, this.Width - 1, this.Height - 1);
            Color fill = !this.Enabled ? Color.FromArgb(180, 192, 210) : (isHovered ? BackColorHover : BackColorNormal);
            using (GraphicsPath path = NexoDraw.RoundedRect(rect, this.Height - 1))
            using (SolidBrush br = new SolidBrush(fill)) {
                e.Graphics.FillPath(br, path);
                if (BorderColor.A > 0) {
                    using (Pen pen = new Pen(BorderColor, 1.2F)) {
                        e.Graphics.DrawPath(pen, path);
                    }
                }
            }
            TextRenderer.DrawText(e.Graphics, this.Text, this.Font, rect, this.Enabled ? this.ForeColor : Color.White, TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        }
    }

    public class PillProgressBar : Control
    {
        private int _val = 0;
        public int Value
        {
            get { return _val; }
            set { _val = Math.Max(0, Math.Min(100, value)); Invalidate(); }
        }
        public ProgressBarStyle Style { get; set; }

        public PillProgressBar()
        {
            this.SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            this.BackColor = Color.Transparent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            Rectangle track = new Rectangle(0, 0, this.Width - 1, this.Height - 1);
            using (GraphicsPath path = NexoDraw.RoundedRect(track, this.Height - 1))
            using (SolidBrush bg = new SolidBrush(Color.FromArgb(226, 234, 245)))
            using (Pen border = new Pen(Color.FromArgb(207, 218, 235), 1F)) {
                e.Graphics.FillPath(bg, path);
                e.Graphics.DrawPath(border, path);
            }
            if (_val > 0) {
                int fillW = Math.Max(this.Height - 2, (int)((this.Width - 3) * (_val / 100.0)));
                Rectangle fillRect = new Rectangle(1, 1, Math.Min(this.Width - 3, fillW), this.Height - 3);
                using (GraphicsPath fp = NexoDraw.RoundedRect(fillRect, fillRect.Height))
                using (SolidBrush fbr = new SolidBrush(Color.FromArgb(242, 140, 40))) {
                    e.Graphics.FillPath(fbr, fp);
                }
            }
        }
    }

    public class UninstallForm : Form
    {
        private Label titleLabel;
        private Label subLabel;
        private Label statusLabel;
        private CheckBox chkRemoveData;
        private PillProgressBar progressBar;
        private PillButton btnUninstall;
        private PillButton btnCancel;

        private string originInstallDir;

        public UninstallForm(string originDir)
        {
            this.originInstallDir = originDir;
            this.Text = "Desinstalar Nexo v__VERSION__";
            this.Size = new Size(520, 315);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(244, 247, 252);
            this.Font = new Font("Segoe UI", 10F);

            try {
                this.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
            } catch {}

            Panel header = new Panel();
            header.Dock = DockStyle.Top;
            header.Height = 80;
            header.BackColor = Color.FromArgb(17, 28, 48);

            if (this.Icon != null) {
                PictureBox pic = new PictureBox();
                pic.Image = this.Icon.ToBitmap();
                pic.SizeMode = PictureBoxSizeMode.Zoom;
                pic.Size = new Size(44, 44);
                pic.Location = new Point(22, 18);
                header.Controls.Add(pic);
            }

            titleLabel = new Label();
            titleLabel.Text = "Desinstalar Nexo v__VERSION__";
            titleLabel.ForeColor = Color.White;
            titleLabel.Font = new Font("Segoe UI", 15.5F, FontStyle.Bold);
            titleLabel.Location = new Point(this.Icon != null ? 76 : 24, 15);
            titleLabel.AutoSize = true;
            header.Controls.Add(titleLabel);

            subLabel = new Label();
            subLabel.Text = "Gestão de Custos, Ficha Técnica e Precificação";
            subLabel.ForeColor = Color.FromArgb(242, 140, 40);
            subLabel.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            subLabel.Location = new Point(this.Icon != null ? 78 : 26, 47);
            subLabel.AutoSize = true;
            header.Controls.Add(subLabel);

            this.Controls.Add(header);

            statusLabel = new Label();
            statusLabel.Text = "Deseja desinstalar o Nexo do seu computador?";
            statusLabel.ForeColor = Color.FromArgb(24, 34, 58);
            statusLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
            statusLabel.Location = new Point(26, 98);
            statusLabel.Size = new Size(455, 24);
            this.Controls.Add(statusLabel);

            chkRemoveData = new CheckBox();
            chkRemoveData.Text = "Apagar também meus dados e cadastros salvos";
            chkRemoveData.Checked = false;
            chkRemoveData.ForeColor = Color.FromArgb(24, 34, 58);
            chkRemoveData.Location = new Point(28, 130);
            chkRemoveData.AutoSize = true;
            this.Controls.Add(chkRemoveData);

            progressBar = new PillProgressBar();
            progressBar.Location = new Point(26, 172);
            progressBar.Size = new Size(452, 16);
            this.Controls.Add(progressBar);

            btnUninstall = new PillButton();
            btnUninstall.Text = "Desinstalar";
            btnUninstall.BackColorNormal = Color.FromArgb(217, 75, 61);
            btnUninstall.BackColorHover = Color.FromArgb(192, 57, 43);
            btnUninstall.ForeColor = Color.White;
            btnUninstall.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            btnUninstall.Location = new Point(338, 214);
            btnUninstall.Size = new Size(140, 36);
            btnUninstall.Click += BtnUninstall_Click;
            this.Controls.Add(btnUninstall);

            btnCancel = new PillButton();
            btnCancel.Text = "Cancelar";
            btnCancel.BackColorNormal = Color.White;
            btnCancel.BackColorHover = Color.FromArgb(236, 241, 249);
            btnCancel.BorderColor = Color.FromArgb(213, 222, 236);
            btnCancel.ForeColor = Color.FromArgb(24, 34, 58);
            btnCancel.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            btnCancel.Location = new Point(228, 214);
            btnCancel.Size = new Size(100, 36);
            btnCancel.Click += (s, e) => this.Close();
            this.Controls.Add(btnCancel);
        }

        public static bool IsAdmin()
        {
            try {
                using (WindowsIdentity id = WindowsIdentity.GetCurrent()) {
                    WindowsPrincipal p = new WindowsPrincipal(id);
                    return p.IsInRole(WindowsBuiltInRole.Administrator);
                }
            } catch {
                return false;
            }
        }

        private List<string> GetInstallDirsToClean()
        {
            List<string> dirs = new List<string>();
            if (!string.IsNullOrEmpty(this.originInstallDir) && Directory.Exists(this.originInstallDir)) {
                dirs.Add(this.originInstallDir);
            }
            try {
                using (RegistryKey baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
                using (RegistryKey key = baseKey.OpenSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Nexo")) {
                    if (key != null) {
                        object val = key.GetValue("InstallLocation");
                        if (val != null && !string.IsNullOrEmpty(val.ToString())) {
                            dirs.Add(val.ToString());
                        }
                    }
                }
            } catch {}

            string pf64 = Environment.GetEnvironmentVariable("ProgramW6432");
            if (!string.IsNullOrEmpty(pf64)) {
                dirs.Add(Path.Combine(pf64, "Nexo"));
            }
            dirs.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Nexo"));
            dirs.Add(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Nexo"));

            string currentDir = Application.StartupPath;
            if (File.Exists(Path.Combine(currentDir, "Nexo.exe")) && !File.Exists(Path.Combine(currentDir, "main.py"))) {
                dirs.Add(currentDir);
            }
            return dirs;
        }

        private static void ForceDeleteDirectory(string targetDir)
        {
            if (string.IsNullOrEmpty(targetDir) || !Directory.Exists(targetDir)) return;
            foreach (string file in Directory.GetFiles(targetDir, "*", SearchOption.AllDirectories)) {
                try {
                    File.SetAttributes(file, FileAttributes.Normal);
                    File.Delete(file);
                } catch {}
            }
            foreach (string subDir in Directory.GetDirectories(targetDir)) {
                try {
                    Directory.Delete(subDir, true);
                } catch {}
            }
            try {
                Directory.Delete(targetDir, true);
            } catch {}
        }

        private async void BtnUninstall_Click(object sender, EventArgs e)
        {
            btnUninstall.Enabled = false;
            btnCancel.Enabled = false;
            chkRemoveData.Enabled = false;
            bool deleteUserData = chkRemoveData.Checked;

            try {
                Environment.CurrentDirectory = Path.GetTempPath();
                List<string> dirsToClean = GetInstallDirsToClean();

                statusLabel.Text = "Encerrando o Nexo...";
                progressBar.Value = 20;
                await Task.Run(() => {
                    foreach (Process proc in Process.GetProcessesByName("Nexo")) {
                        try { proc.Kill(); proc.WaitForExit(3000); } catch {}
                    }
                    Thread.Sleep(300);
                });

                statusLabel.Text = "Removendo atalhos...";
                progressBar.Value = 40;
                await Task.Run(() => {
                    string[] desktops = new string[] {
                        Environment.GetFolderPath(Environment.SpecialFolder.CommonDesktopDirectory),
                        Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory)
                    };
                    foreach (string d in desktops) {
                        if (!string.IsNullOrEmpty(d)) {
                            string lnk = Path.Combine(d, "Nexo.lnk");
                            if (File.Exists(lnk)) { try { File.Delete(lnk); } catch {} }
                        }
                    }

                    string[] startMenus = new string[] {
                        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonPrograms), "Nexo"),
                        Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Nexo")
                    };
                    foreach (string sm in startMenus) {
                        if (Directory.Exists(sm)) { try { Directory.Delete(sm, true); } catch {} }
                    }
                    Thread.Sleep(200);
                });

                if (deleteUserData) {
                    statusLabel.Text = "Removendo dados e cadastros salvos...";
                    progressBar.Value = 60;
                    await Task.Run(() => {
                        string userDataDir = Path.Combine(
                            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                            "Nexo"
                        );
                        if (Directory.Exists(userDataDir)) {
                            ForceDeleteDirectory(userDataDir);
                        }
                        Thread.Sleep(200);
                    });
                }

                statusLabel.Text = "Removendo arquivos do programa...";
                progressBar.Value = 85;
                await Task.Run(() => {
                    foreach (string d in dirsToClean) {
                        if (string.IsNullOrEmpty(d) || !Directory.Exists(d)) continue;
                        if (File.Exists(Path.Combine(d, "main.py"))) continue;
                        ForceDeleteDirectory(d);
                    }
                    Thread.Sleep(250);
                });

                statusLabel.Text = "Limpando registros do sistema...";
                progressBar.Value = 100;
                await Task.Run(() => {
                    try {
                        using (RegistryKey baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64)) {
                            baseKey.DeleteSubKeyTree(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Nexo", false);
                        }
                    } catch {}
                    try {
                        Registry.LocalMachine.DeleteSubKeyTree(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Nexo", false);
                    } catch {}
                    try {
                        Registry.CurrentUser.DeleteSubKeyTree(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Nexo", false);
                    } catch {}
                    Thread.Sleep(200);
                });

                MessageBox.Show(
                    "O Nexo foi desinstalado com sucesso.",
                    "Desinstalação Concluída",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );

                this.Hide();
                Application.DoEvents();

                // Se ainda restar a pasta de origem ou o executavel temporario, limpa via cmd em %TEMP%
                foreach (string d in dirsToClean) {
                    if (!string.IsNullOrEmpty(d) && Directory.Exists(d) && !File.Exists(Path.Combine(d, "main.py"))) {
                        try {
                            ProcessStartInfo cmd = new ProcessStartInfo("cmd.exe", "/c ping 127.0.0.1 -n 3 > NUL & rmdir /s /q \"" + d + "\"");
                            cmd.WorkingDirectory = Path.GetTempPath();
                            cmd.WindowStyle = ProcessWindowStyle.Hidden;
                            cmd.CreateNoWindow = true;
                            Process.Start(cmd);
                        } catch {}
                    }
                }
                Environment.Exit(0);
            }
            catch (Exception ex) {
                MessageBox.Show("Erro ao desinstalar:\n" + ex.Message, "Erro", MessageBoxButtons.OK, MessageBoxIcon.Error);
                btnUninstall.Enabled = true;
                btnCancel.Enabled = true;
            }
        }

        [STAThread]
        public static void Main(string[] args)
        {
            if (!IsAdmin()) {
                try {
                    ProcessStartInfo psi = new ProcessStartInfo(Application.ExecutablePath);
                    if (args != null && args.Length > 0) {
                        psi.Arguments = "\"" + args[0] + "\"";
                    }
                    psi.Verb = "runas";
                    Process.Start(psi);
                } catch {}
                return;
            }

            // Padrao oficial de desinstaladores Windows (Inno Setup / NSIS):
            // Se o desinstalador foi iniciado de dentro da pasta instalada (onde existe Nexo.exe),
            // copia a si mesmo para %TEMP% e executa de la para nao travar a pasta C:\Program Files\Nexo!
            string currentDir = Path.GetFullPath(Application.StartupPath).TrimEnd('\\');
            string tempDir = Path.GetFullPath(Path.GetTempPath()).TrimEnd('\\');
            string originDir = (args != null && args.Length > 0) ? args[0] : "";

            if (File.Exists(Path.Combine(currentDir, "Nexo.exe")) &&
                !File.Exists(Path.Combine(currentDir, "main.py")) &&
                !currentDir.StartsWith(tempDir, StringComparison.OrdinalIgnoreCase))
            {
                try {
                    string tempExe = Path.Combine(tempDir, "Nexo_Uninstaller_" + Guid.NewGuid().ToString("N") + ".exe");
                    File.Copy(Application.ExecutablePath, tempExe, true);
                    ProcessStartInfo psi = new ProcessStartInfo(tempExe, "\"" + currentDir + "\"");
                    psi.WorkingDirectory = tempDir;
                    Process.Start(psi);
                    return;
                } catch {}
            }

            Environment.CurrentDirectory = tempDir;
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new UninstallForm(originDir));
        }
    }
}
'''

CSHARP_INSTALLER_TEMPLATE = r'''
using System;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Security.Principal;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Win32;

[assembly: AssemblyTitle("Nexo - Gestão de Custos e Precificação")]
[assembly: AssemblyDescription("Instalador do Nexo v__VERSION__ (x64)")]
[assembly: AssemblyCompany("Leonan Garcia")]
[assembly: AssemblyProduct("Nexo")]
[assembly: AssemblyCopyright("© 2026 Leonan Garcia. Todos os direitos reservados.")]
[assembly: AssemblyVersion("__VERSION__.0")]
[assembly: AssemblyFileVersion("__VERSION__.0")]

namespace NexoSetup
{
    public static class NexoDraw
    {
        public static GraphicsPath RoundedRect(Rectangle bounds, int radius)
        {
            GraphicsPath path = new GraphicsPath();
            int d = Math.Min(radius, Math.Min(bounds.Width, bounds.Height));
            if (d <= 0) {
                path.AddRectangle(bounds);
                return path;
            }
            Rectangle arc = new Rectangle(bounds.Location, new Size(d, d));
            path.AddArc(arc, 180, 90);
            arc.X = bounds.Right - d;
            path.AddArc(arc, 270, 90);
            arc.Y = bounds.Bottom - d;
            path.AddArc(arc, 0, 90);
            arc.X = bounds.Left;
            path.AddArc(arc, 90, 90);
            path.CloseFigure();
            return path;
        }
    }

    public class PillButton : Control
    {
        public Color BackColorNormal { get; set; }
        public Color BackColorHover { get; set; }
        public Color BorderColor { get; set; }
        private bool isHovered = false;

        public PillButton()
        {
            this.SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            this.BackColor = Color.Transparent;
            this.Cursor = Cursors.Hand;
            this.BackColorNormal = Color.FromArgb(242, 140, 40);
            this.BackColorHover = Color.FromArgb(223, 123, 23);
            this.BorderColor = Color.Transparent;
        }

        protected override void OnMouseEnter(EventArgs e) { isHovered = true; Invalidate(); base.OnMouseEnter(e); }
        protected override void OnMouseLeave(EventArgs e) { isHovered = false; Invalidate(); base.OnMouseLeave(e); }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            Rectangle rect = new Rectangle(0, 0, this.Width - 1, this.Height - 1);
            Color fill = !this.Enabled ? Color.FromArgb(180, 192, 210) : (isHovered ? BackColorHover : BackColorNormal);
            using (GraphicsPath path = NexoDraw.RoundedRect(rect, this.Height - 1))
            using (SolidBrush br = new SolidBrush(fill)) {
                e.Graphics.FillPath(br, path);
                if (BorderColor.A > 0) {
                    using (Pen pen = new Pen(BorderColor, 1.2F)) {
                        e.Graphics.DrawPath(pen, path);
                    }
                }
            }
            TextRenderer.DrawText(e.Graphics, this.Text, this.Font, rect, this.Enabled ? this.ForeColor : Color.White, TextFormatFlags.HorizontalCenter | TextFormatFlags.VerticalCenter);
        }
    }

    public class PillProgressBar : Control
    {
        private int _val = 0;
        public int Value
        {
            get { return _val; }
            set { _val = Math.Max(0, Math.Min(100, value)); Invalidate(); }
        }
        public ProgressBarStyle Style { get; set; }

        public PillProgressBar()
        {
            this.SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            this.BackColor = Color.Transparent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            Rectangle track = new Rectangle(0, 0, this.Width - 1, this.Height - 1);
            using (GraphicsPath path = NexoDraw.RoundedRect(track, this.Height - 1))
            using (SolidBrush bg = new SolidBrush(Color.FromArgb(226, 234, 245)))
            using (Pen border = new Pen(Color.FromArgb(207, 218, 235), 1F)) {
                e.Graphics.FillPath(bg, path);
                e.Graphics.DrawPath(border, path);
            }
            if (_val > 0) {
                int fillW = Math.Max(this.Height - 2, (int)((this.Width - 3) * (_val / 100.0)));
                Rectangle fillRect = new Rectangle(1, 1, Math.Min(this.Width - 3, fillW), this.Height - 3);
                using (GraphicsPath fp = NexoDraw.RoundedRect(fillRect, fillRect.Height))
                using (SolidBrush fbr = new SolidBrush(Color.FromArgb(242, 140, 40))) {
                    e.Graphics.FillPath(fbr, fp);
                }
            }
        }
    }

    public class PillPanel : Panel
    {
        public PillPanel()
        {
            this.SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            this.BackColor = Color.Transparent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            e.Graphics.SmoothingMode = SmoothingMode.AntiAlias;
            Rectangle rect = new Rectangle(0, 0, this.Width - 1, this.Height - 1);
            using (GraphicsPath path = NexoDraw.RoundedRect(rect, this.Height - 1))
            using (SolidBrush br = new SolidBrush(Color.White))
            using (Pen pen = new Pen(Color.FromArgb(213, 222, 236), 1.2F)) {
                e.Graphics.FillPath(br, path);
                e.Graphics.DrawPath(pen, path);
            }
        }
    }

    public class HighQualityLogoBox : Control
    {
        public Image LogoImage { get; set; }

        public HighQualityLogoBox()
        {
            this.SetStyle(ControlStyles.AllPaintingInWmPaint | ControlStyles.UserPaint | ControlStyles.OptimizedDoubleBuffer | ControlStyles.ResizeRedraw | ControlStyles.SupportsTransparentBackColor, true);
            this.BackColor = Color.Transparent;
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            if (LogoImage == null) return;
            e.Graphics.InterpolationMode = InterpolationMode.HighQualityBicubic;
            e.Graphics.SmoothingMode = SmoothingMode.HighQuality;
            e.Graphics.PixelOffsetMode = PixelOffsetMode.HighQuality;
            e.Graphics.CompositingQuality = CompositingQuality.HighQuality;

            double ratioX = (double)this.Width / LogoImage.Width;
            double ratioY = (double)this.Height / LogoImage.Height;
            double ratio = Math.Min(ratioX, ratioY);
            int w = (int)(LogoImage.Width * ratio);
            int h = (int)(LogoImage.Height * ratio);
            int x = (this.Width - w) / 2;
            int y = (this.Height - h) / 2;
            e.Graphics.DrawImage(LogoImage, new Rectangle(x, y, w, h));
        }
    }

    public class SetupForm : Form
    {
        private int currentStep = 0;
        private Panel[] stepPanels;
        private Label stepLabel;

        // Passo 1: Pasta de instalacao
        private TextBox txtInstallDir;
        private PillButton btnBrowse;

        // Passo 2: Local do banco de dados
        private RadioButton rbDbDefault;
        private RadioButton rbDbCustom;
        private TextBox txtDbDir;
        private PillButton btnDbBrowse;

        // Passo 3: Opcoes de acesso
        private RadioButton rbAllUsers;
        private RadioButton rbCurrentUser;

        // Passo 4: Opcoes extras & Instalacao
        private CheckBox chkDesktop;
        private CheckBox chkLaunch;
        private PillProgressBar progressBar;

        private PillButton btnBack;
        private PillButton btnNext;
        private PillButton btnInstall;
        private PillButton btnCancel;
        private bool cleanInstallDir = false;
        private bool resetExistingDb = false;

        public static string GetDefaultProgramFilesDir()
        {
            string pf64 = Environment.GetEnvironmentVariable("ProgramW6432");
            if (!string.IsNullOrEmpty(pf64) && Directory.Exists(pf64)) {
                return Path.Combine(pf64, "Nexo");
            }
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Nexo");
        }

        public static string GetDefaultUserDataDir()
        {
            return Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "Nexo"
            );
        }

        public SetupForm()
        {
            this.Text = "Instalador do Nexo v__VERSION__ (x64)";
            this.Size = new Size(540, 496);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(244, 247, 252);
            this.Font = new Font("Segoe UI", 8.5F);

            try {
                this.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
            } catch {}

            // Logo completa grande estilo Avast, centralizada e em alta qualidade
            HighQualityLogoBox logoBox = new HighQualityLogoBox();
            logoBox.Size = new Size(380, 278);
            logoBox.Location = new Point((this.ClientSize.Width - logoBox.Width) / 2, 8);
            try {
                Assembly asm = Assembly.GetExecutingAssembly();
                using (Stream imgStream = asm.GetManifestResourceStream("nexo_about_light.png")) {
                    if (imgStream != null) {
                        logoBox.LogoImage = Image.FromStream(imgStream);
                    }
                }
            } catch {}
            this.Controls.Add(logoBox);

            // Indicador sutil de etapa
            stepLabel = new Label();
            stepLabel.ForeColor = Color.FromArgb(130, 146, 174);
            stepLabel.Font = new Font("Segoe UI", 8F, FontStyle.Bold);
            stepLabel.TextAlign = ContentAlignment.MiddleCenter;
            stepLabel.Location = new Point(28, 290);
            stepLabel.Size = new Size(468, 16);
            this.Controls.Add(stepLabel);

            stepPanels = new Panel[4];
            for (int i = 0; i < 4; i++) {
                Panel p = new Panel();
                p.Location = new Point(28, 310);
                p.Size = new Size(468, 102);
                p.BackColor = Color.Transparent;
                p.Visible = (i == 0);
                this.Controls.Add(p);
                stepPanels[i] = p;
            }

            // === PASSO 1: Pasta de instalacao ===
            Label lblDir = new Label();
            lblDir.Text = "Pasta de instalação do Nexo:";
            lblDir.ForeColor = Color.FromArgb(24, 34, 58);
            lblDir.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            lblDir.Location = new Point(0, 6);
            lblDir.AutoSize = true;
            stepPanels[0].Controls.Add(lblDir);

            Label lblDirHint = new Label();
            lblDirHint.Text = "Escolha onde os arquivos do programa serão instalados.";
            lblDirHint.ForeColor = Color.FromArgb(110, 126, 154);
            lblDirHint.Font = new Font("Segoe UI", 8F);
            lblDirHint.Location = new Point(0, 24);
            lblDirHint.AutoSize = true;
            stepPanels[0].Controls.Add(lblDirHint);

            PillPanel dirBox = new PillPanel();
            dirBox.Location = new Point(0, 48);
            dirBox.Size = new Size(372, 28);
            stepPanels[0].Controls.Add(dirBox);

            txtInstallDir = new TextBox();
            txtInstallDir.Text = GetDefaultProgramFilesDir();
            txtInstallDir.BorderStyle = BorderStyle.None;
            txtInstallDir.BackColor = Color.White;
            txtInstallDir.ForeColor = Color.FromArgb(24, 34, 58);
            txtInstallDir.Location = new Point(12, 6);
            txtInstallDir.Size = new Size(348, 16);
            txtInstallDir.Font = new Font("Segoe UI", 8.5F);
            dirBox.Controls.Add(txtInstallDir);

            btnBrowse = new PillButton();
            btnBrowse.Text = "Procurar...";
            btnBrowse.BackColorNormal = Color.White;
            btnBrowse.BackColorHover = Color.FromArgb(236, 241, 249);
            btnBrowse.BorderColor = Color.FromArgb(213, 222, 236);
            btnBrowse.ForeColor = Color.FromArgb(24, 34, 58);
            btnBrowse.Font = new Font("Segoe UI", 8.2F, FontStyle.Bold);
            btnBrowse.Location = new Point(380, 48);
            btnBrowse.Size = new Size(88, 28);
            btnBrowse.Click += BtnBrowse_Click;
            stepPanels[0].Controls.Add(btnBrowse);

            // === PASSO 2: Local do Banco de Dados ===
            Label lblDb = new Label();
            lblDb.Text = "Local do Banco de Dados (nexo.db):";
            lblDb.ForeColor = Color.FromArgb(24, 34, 58);
            lblDb.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            lblDb.Location = new Point(0, 2);
            lblDb.AutoSize = true;
            stepPanels[1].Controls.Add(lblDb);

            rbDbDefault = new RadioButton();
            rbDbDefault.Text = "Usar pasta padrão do sistema (Recomendado)";
            rbDbDefault.Checked = true;
            rbDbDefault.Font = new Font("Segoe UI", 8.5F);
            rbDbDefault.ForeColor = Color.FromArgb(24, 34, 58);
            rbDbDefault.Location = new Point(2, 24);
            rbDbDefault.AutoSize = true;
            rbDbDefault.CheckedChanged += (s, e) => UpdateDbDirState();
            stepPanels[1].Controls.Add(rbDbDefault);

            rbDbCustom = new RadioButton();
            rbDbCustom.Text = "Escolher outra pasta (ex: outro HD ou nuvem)";
            rbDbCustom.Checked = false;
            rbDbCustom.Font = new Font("Segoe UI", 8.5F);
            rbDbCustom.ForeColor = Color.FromArgb(24, 34, 58);
            rbDbCustom.Location = new Point(2, 46);
            rbDbCustom.AutoSize = true;
            rbDbCustom.CheckedChanged += (s, e) => UpdateDbDirState();
            stepPanels[1].Controls.Add(rbDbCustom);

            PillPanel dbBox = new PillPanel();
            dbBox.Location = new Point(0, 70);
            dbBox.Size = new Size(372, 28);
            stepPanels[1].Controls.Add(dbBox);

            txtDbDir = new TextBox();
            txtDbDir.Text = GetDefaultUserDataDir();
            txtDbDir.BorderStyle = BorderStyle.None;
            txtDbDir.BackColor = Color.White;
            txtDbDir.ForeColor = Color.FromArgb(24, 34, 58);
            txtDbDir.Location = new Point(12, 6);
            txtDbDir.Size = new Size(348, 16);
            txtDbDir.Font = new Font("Segoe UI", 8.5F);
            dbBox.Controls.Add(txtDbDir);

            btnDbBrowse = new PillButton();
            btnDbBrowse.Text = "Procurar...";
            btnDbBrowse.BackColorNormal = Color.White;
            btnDbBrowse.BackColorHover = Color.FromArgb(236, 241, 249);
            btnDbBrowse.BorderColor = Color.FromArgb(213, 222, 236);
            btnDbBrowse.ForeColor = Color.FromArgb(24, 34, 58);
            btnDbBrowse.Font = new Font("Segoe UI", 8.2F, FontStyle.Bold);
            btnDbBrowse.Location = new Point(380, 70);
            btnDbBrowse.Size = new Size(88, 28);
            btnDbBrowse.Click += BtnDbBrowse_Click;
            stepPanels[1].Controls.Add(btnDbBrowse);
            UpdateDbDirState();

            // === PASSO 3: Opcoes de acesso ===
            Label lblScope = new Label();
            lblScope.Text = "Opções de acesso:";
            lblScope.ForeColor = Color.FromArgb(24, 34, 58);
            lblScope.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            lblScope.Location = new Point(0, 6);
            lblScope.AutoSize = true;
            stepPanels[2].Controls.Add(lblScope);

            Label lblScopeHint = new Label();
            lblScopeHint.Text = "Defina para quais usuários do Windows os atalhos serão criados.";
            lblScopeHint.ForeColor = Color.FromArgb(110, 126, 154);
            lblScopeHint.Font = new Font("Segoe UI", 8F);
            lblScopeHint.Location = new Point(0, 24);
            lblScopeHint.AutoSize = true;
            stepPanels[2].Controls.Add(lblScopeHint);

            rbAllUsers = new RadioButton();
            rbAllUsers.Text = "Todos os usuários (Padrão)";
            rbAllUsers.Checked = true;
            rbAllUsers.Font = new Font("Segoe UI", 8.5F);
            rbAllUsers.ForeColor = Color.FromArgb(24, 34, 58);
            rbAllUsers.Location = new Point(2, 48);
            rbAllUsers.AutoSize = true;
            stepPanels[2].Controls.Add(rbAllUsers);

            rbCurrentUser = new RadioButton();
            rbCurrentUser.Text = "Apenas para mim";
            rbCurrentUser.Checked = false;
            rbCurrentUser.Font = new Font("Segoe UI", 8.5F);
            rbCurrentUser.ForeColor = Color.FromArgb(24, 34, 58);
            rbCurrentUser.Location = new Point(2, 72);
            rbCurrentUser.AutoSize = true;
            stepPanels[2].Controls.Add(rbCurrentUser);

            // === PASSO 4: Opcoes extras & Progresso ===
            Label lblOpt = new Label();
            lblOpt.Text = "Opções finais:";
            lblOpt.ForeColor = Color.FromArgb(24, 34, 58);
            lblOpt.Font = new Font("Segoe UI", 9F, FontStyle.Bold);
            lblOpt.Location = new Point(0, 4);
            lblOpt.AutoSize = true;
            stepPanels[3].Controls.Add(lblOpt);

            chkDesktop = new CheckBox();
            chkDesktop.Text = "Criar atalho na Área de Trabalho";
            chkDesktop.Checked = true;
            chkDesktop.Font = new Font("Segoe UI", 8.5F);
            chkDesktop.ForeColor = Color.FromArgb(24, 34, 58);
            chkDesktop.Location = new Point(2, 26);
            chkDesktop.AutoSize = true;
            stepPanels[3].Controls.Add(chkDesktop);

            chkLaunch = new CheckBox();
            chkLaunch.Text = "Abrir o Nexo ao finalizar";
            chkLaunch.Checked = true;
            chkLaunch.Font = new Font("Segoe UI", 8.5F);
            chkLaunch.ForeColor = Color.FromArgb(24, 34, 58);
            chkLaunch.Location = new Point(2, 48);
            chkLaunch.AutoSize = true;
            stepPanels[3].Controls.Add(chkLaunch);

            progressBar = new PillProgressBar();
            progressBar.Location = new Point(0, 78);
            progressBar.Size = new Size(468, 14);
            stepPanels[3].Controls.Add(progressBar);

            // Linha sutil acima dos botoes
            Panel divider = new Panel();
            divider.Location = new Point(28, 414);
            divider.Size = new Size(468, 1);
            divider.BackColor = Color.FromArgb(224, 232, 244);
            this.Controls.Add(divider);

            // Rodape de navegacao compacto
            btnCancel = new PillButton();
            btnCancel.Text = "Cancelar";
            btnCancel.BackColorNormal = Color.White;
            btnCancel.BackColorHover = Color.FromArgb(236, 241, 249);
            btnCancel.BorderColor = Color.FromArgb(213, 222, 236);
            btnCancel.ForeColor = Color.FromArgb(96, 118, 157);
            btnCancel.Font = new Font("Segoe UI", 8.5F, FontStyle.Bold);
            btnCancel.Location = new Point(28, 425);
            btnCancel.Size = new Size(86, 30);
            btnCancel.Click += (s, e) => this.Close();
            this.Controls.Add(btnCancel);

            btnBack = new PillButton();
            btnBack.Text = "Voltar";
            btnBack.BackColorNormal = Color.White;
            btnBack.BackColorHover = Color.FromArgb(236, 241, 249);
            btnBack.BorderColor = Color.FromArgb(213, 222, 236);
            btnBack.ForeColor = Color.FromArgb(24, 34, 58);
            btnBack.Font = new Font("Segoe UI", 8.5F, FontStyle.Bold);
            btnBack.Location = new Point(296, 425);
            btnBack.Size = new Size(82, 30);
            btnBack.Click += (s, e) => ShowStep(currentStep - 1);
            this.Controls.Add(btnBack);

            btnNext = new PillButton();
            btnNext.Text = "Avançar";
            btnNext.BackColorNormal = Color.FromArgb(242, 140, 40);
            btnNext.BackColorHover = Color.FromArgb(223, 123, 23);
            btnNext.ForeColor = Color.White;
            btnNext.Font = new Font("Segoe UI", 8.5F, FontStyle.Bold);
            btnNext.Location = new Point(386, 425);
            btnNext.Size = new Size(110, 30);
            btnNext.Click += (s, e) => HandleNextClick();
            this.Controls.Add(btnNext);

            btnInstall = new PillButton();
            btnInstall.Text = "Instalar";
            btnInstall.BackColorNormal = Color.FromArgb(242, 140, 40);
            btnInstall.BackColorHover = Color.FromArgb(223, 123, 23);
            btnInstall.ForeColor = Color.White;
            btnInstall.Font = new Font("Segoe UI", 8.8F, FontStyle.Bold);
            btnInstall.Location = new Point(386, 425);
            btnInstall.Size = new Size(110, 30);
            btnInstall.Click += BtnInstall_Click;
            this.Controls.Add(btnInstall);

            ShowStep(0);
        }

        private void ShowStep(int step)
        {
            currentStep = Math.Max(0, Math.Min(3, step));
            for (int i = 0; i < stepPanels.Length; i++) {
                stepPanels[i].Visible = (i == currentStep);
            }
            string[] names = new string[] {
                "Passo 1 de 4  •  Local de Instalação",
                "Passo 2 de 4  •  Banco de Dados",
                "Passo 3 de 4  •  Opções de Acesso",
                "Passo 4 de 4  •  Finalizar Instalação"
            };
            stepLabel.Text = names[currentStep];
            btnBack.Visible = (currentStep > 0);
            btnNext.Visible = (currentStep < 3);
            btnInstall.Visible = (currentStep == 3);
        }

        private void UpdateDbDirState()
        {
            bool custom = rbDbCustom.Checked;
            txtDbDir.Enabled = custom;
            btnDbBrowse.Enabled = custom;
            txtDbDir.ForeColor = custom ? Color.FromArgb(24, 34, 58) : Color.FromArgb(140, 155, 181);
        }

        private void BtnDbBrowse_Click(object sender, EventArgs e)
        {
            using (FolderBrowserDialog fbd = new FolderBrowserDialog()) {
                fbd.Description = "Selecione a pasta onde o banco de dados (nexo.db) será salvo:";
                fbd.SelectedPath = txtDbDir.Text;
                if (fbd.ShowDialog(this) == DialogResult.OK && !string.IsNullOrWhiteSpace(fbd.SelectedPath)) {
                    txtDbDir.Text = fbd.SelectedPath.Trim().TrimEnd('\\');
                }
            }
        }

        private void BtnBrowse_Click(object sender, EventArgs e)
        {
            using (FolderBrowserDialog fbd = new FolderBrowserDialog()) {
                fbd.Description = "Selecione a pasta onde deseja instalar o Nexo:";
                fbd.SelectedPath = txtInstallDir.Text;
                if (fbd.ShowDialog(this) == DialogResult.OK && !string.IsNullOrWhiteSpace(fbd.SelectedPath)) {
                    string chosen = fbd.SelectedPath.Trim().TrimEnd('\\');
                    if (!chosen.EndsWith("\\Nexo", StringComparison.OrdinalIgnoreCase) && !string.Equals(Path.GetFileName(chosen), "Nexo", StringComparison.OrdinalIgnoreCase)) {
                        chosen = Path.Combine(chosen, "Nexo");
                    }
                    txtInstallDir.Text = chosen;
                }
            }
        }

        private void HandleNextClick()
        {
            if (currentStep == 0) {
                string rawDir = txtInstallDir.Text.Trim();
                if (string.IsNullOrEmpty(rawDir)) {
                    MessageBox.Show("Informe uma pasta válida para a instalação.", "Atenção", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
                string installDir = Path.GetFullPath(rawDir).TrimEnd('\\');
                if (!installDir.EndsWith("\\Nexo", StringComparison.OrdinalIgnoreCase) && !string.Equals(Path.GetFileName(installDir), "Nexo", StringComparison.OrdinalIgnoreCase)) {
                    installDir = Path.Combine(installDir, "Nexo");
                    txtInstallDir.Text = installDir;
                }
                if (File.Exists(Path.Combine(installDir, "main.py"))) {
                    MessageBox.Show("A pasta selecionada contém o código-fonte do projeto. Escolha outra pasta para instalar o aplicativo.", "Pasta Inválida", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
                cleanInstallDir = false;
                if (Directory.Exists(installDir) && (Directory.GetFiles(installDir).Length > 0 || Directory.GetDirectories(installDir).Length > 0)) {
                    DialogResult res = MessageBox.Show(
                        "A pasta de instalação selecionada já existe e contém arquivos:\n\n" + installDir +
                        "\n\nDeseja LIMPAR toda a pasta e recriar do zero?\n\n" +
                        "• Sim = Limpar a pasta e recriar tudo\n" +
                        "• Não = Reutilizar a pasta (atualizar os arquivos do Nexo)\n" +
                        "• Cancelar = Escolher outra pasta",
                        "Pasta Já Existente",
                        MessageBoxButtons.YesNoCancel,
                        MessageBoxIcon.Question
                    );
                    if (res == DialogResult.Cancel) return;
                    cleanInstallDir = (res == DialogResult.Yes);
                }
            } else if (currentStep == 1) {
                string targetDbDir = GetDefaultUserDataDir();
                if (rbDbCustom.Checked) {
                    string rawDb = txtDbDir.Text.Trim();
                    if (string.IsNullOrEmpty(rawDb)) {
                        MessageBox.Show("Informe uma pasta válida para o banco de dados.", "Atenção", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                        return;
                    }
                    targetDbDir = Path.GetFullPath(rawDb).TrimEnd('\\');
                }
                resetExistingDb = false;
                bool hasOldDb = File.Exists(Path.Combine(targetDbDir, "nexo.db"))
                    || Directory.Exists(Path.Combine(targetDbDir, "backups"))
                    || Directory.Exists(Path.Combine(targetDbDir, "documentos"));
                if (hasOldDb) {
                    DialogResult res = MessageBox.Show(
                        "Já existem dados ou banco de dados (nexo.db) nesta pasta:\n\n" + targetDbDir +
                        "\n\nDeseja APAGAR os dados antigos e começar do zero (padrão de fábrica)?\n\n" +
                        "• Sim = Apagar banco, backups e configurações antigas\n" +
                        "• Não = Reutilizar os dados existentes (Recomendado)\n" +
                        "• Cancelar = Escolher outra pasta",
                        "Banco de Dados Já Existente",
                        MessageBoxButtons.YesNoCancel,
                        MessageBoxIcon.Question
                    );
                    if (res == DialogResult.Cancel) return;
                    resetExistingDb = (res == DialogResult.Yes);
                }
            }
            ShowStep(currentStep + 1);
        }

        public static bool IsAdmin()
        {
            try {
                using (WindowsIdentity id = WindowsIdentity.GetCurrent()) {
                    WindowsPrincipal p = new WindowsPrincipal(id);
                    return p.IsInRole(WindowsBuiltInRole.Administrator);
                }
            } catch {
                return false;
            }
        }

        private async void BtnInstall_Click(object sender, EventArgs e)
        {
            string rawDir = txtInstallDir.Text.Trim();
            if (string.IsNullOrEmpty(rawDir)) {
                MessageBox.Show("Informe uma pasta válida para a instalação.", "Atenção", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            string installDir = Path.GetFullPath(rawDir).TrimEnd('\\');
            if (!installDir.EndsWith("\\Nexo", StringComparison.OrdinalIgnoreCase) && !string.Equals(Path.GetFileName(installDir), "Nexo", StringComparison.OrdinalIgnoreCase)) {
                installDir = Path.Combine(installDir, "Nexo");
                txtInstallDir.Text = installDir;
            }

            // Protecao para nao sobrescrever uma pasta de codigo-fonte
            if (File.Exists(Path.Combine(installDir, "main.py"))) {
                MessageBox.Show("A pasta selecionada contém o código-fonte do projeto. Escolha outra pasta para instalar o aplicativo.", "Pasta Inválida", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            btnInstall.Enabled = false;
            btnBack.Enabled = false;
            btnNext.Enabled = false;
            btnCancel.Enabled = false;
            btnBrowse.Enabled = false;
            txtInstallDir.Enabled = false;
            rbDbDefault.Enabled = false;
            rbDbCustom.Enabled = false;
            txtDbDir.Enabled = false;
            btnDbBrowse.Enabled = false;
            rbAllUsers.Enabled = false;
            rbCurrentUser.Enabled = false;
            chkDesktop.Enabled = false;
            chkLaunch.Enabled = false;
            progressBar.Value = 20;

            bool allUsers = rbAllUsers.Checked;
            bool useCustomDb = rbDbCustom.Checked && !string.IsNullOrWhiteSpace(txtDbDir.Text);
            string customDbDir = useCustomDb ? Path.GetFullPath(txtDbDir.Text.Trim()).TrimEnd('\\') : "";
            bool doCleanInstall = cleanInstallDir;
            bool doResetDb = resetExistingDb;

            try {
                await Task.Run(() => {
                    foreach (Process proc in Process.GetProcessesByName("Nexo")) {
                        try { proc.Kill(); proc.WaitForExit(2000); } catch {}
                    }
                    if (doCleanInstall && Directory.Exists(installDir)) {
                        try { Directory.Delete(installDir, true); } catch {}
                    }
                    Directory.CreateDirectory(installDir);

                    string userDataDir = GetDefaultUserDataDir();
                    string targetDbDir = useCustomDb ? customDbDir : userDataDir;
                    if (doResetDb) {
                        string[] dbFiles = new string[] {
                            "nexo.db", "nexo.db-wal", "nexo.db-shm",
                            "nexo_config.json", "nexo_file_config.json"
                        };
                        foreach (string f in dbFiles) {
                            string p = Path.Combine(targetDbDir, f);
                            if (File.Exists(p)) { try { File.Delete(p); } catch {} }
                        }
                        foreach (string sub in new string[] { "backups", "documentos" }) {
                            string sp = Path.Combine(targetDbDir, sub);
                            if (Directory.Exists(sp)) { try { Directory.Delete(sp, true); } catch {} }
                        }
                    }

                    Directory.CreateDirectory(userDataDir);
                    Directory.CreateDirectory(Path.Combine(userDataDir, "backups"));
                    Directory.CreateDirectory(Path.Combine(userDataDir, "documentos"));

                    string fileCfgPath = Path.Combine(userDataDir, "nexo_file_config.json");
                    if (useCustomDb) {
                        Directory.CreateDirectory(customDbDir);
                        Directory.CreateDirectory(Path.Combine(customDbDir, "backups"));
                        Directory.CreateDirectory(Path.Combine(customDbDir, "documentos"));
                        string dbFull = Path.Combine(customDbDir, "nexo.db").Replace("\\", "\\\\");
                        File.WriteAllText(fileCfgPath, "{\n  \"sqlite_path\": \"" + dbFull + "\"\n}");
                    } else if (File.Exists(fileCfgPath)) {
                        try { File.Delete(fileCfgPath); } catch {}
                    }

                    Assembly asm = Assembly.GetExecutingAssembly();
                    using (Stream s = asm.GetManifestResourceStream("payload.zip")) {
                        string tempZip = Path.Combine(Path.GetTempPath(), "nexo_payload_" + Guid.NewGuid().ToString("N") + ".zip");
                        using (FileStream fs = new FileStream(tempZip, FileMode.Create, FileAccess.Write)) {
                            s.CopyTo(fs);
                        }
                        using (ZipArchive archive = ZipFile.OpenRead(tempZip)) {
                            foreach (ZipArchiveEntry entry in archive.Entries) {
                                string destPath = Path.GetFullPath(Path.Combine(installDir, entry.FullName));
                                if (!destPath.StartsWith(installDir, StringComparison.OrdinalIgnoreCase)) continue;
                                if (string.IsNullOrEmpty(entry.Name)) {
                                    Directory.CreateDirectory(destPath);
                                } else {
                                    Directory.CreateDirectory(Path.GetDirectoryName(destPath));
                                    entry.ExtractToFile(destPath, true);
                                }
                            }
                        }
                        try { File.Delete(tempZip); } catch {}
                    }
                });

                progressBar.Value = 80;

                string exePath = Path.Combine(installDir, "Nexo.exe");
                string uninstallPath = Path.Combine(installDir, "Uninstall_Nexo.exe");
                string iconPath = Path.Combine(installDir, "nexo_icon.ico");

                // Limpa atalhos antigos antes de criar o novo (garante que nunca duplique)
                string commonDesktop = Environment.GetFolderPath(Environment.SpecialFolder.CommonDesktopDirectory);
                string userDesktop = Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory);
                if (!string.IsNullOrEmpty(commonDesktop) && File.Exists(Path.Combine(commonDesktop, "Nexo.lnk"))) {
                    try { File.Delete(Path.Combine(commonDesktop, "Nexo.lnk")); } catch {}
                }
                if (!string.IsNullOrEmpty(userDesktop) && File.Exists(Path.Combine(userDesktop, "Nexo.lnk"))) {
                    try { File.Delete(Path.Combine(userDesktop, "Nexo.lnk")); } catch {}
                }

                string commonStartMenu = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonPrograms), "Nexo");
                string userStartMenu = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs), "Nexo");
                if (Directory.Exists(commonStartMenu)) { try { Directory.Delete(commonStartMenu, true); } catch {} }
                if (Directory.Exists(userStartMenu)) { try { Directory.Delete(userStartMenu, true); } catch {} }

                // Cria atalhos apenas no escopo selecionado (Todos os usuarios OU Apenas para mim)
                string targetStartMenu = allUsers ? commonStartMenu : userStartMenu;
                try {
                    Directory.CreateDirectory(targetStartMenu);
                    CreateShortcut(Path.Combine(targetStartMenu, "Nexo.lnk"), exePath, installDir, iconPath);
                    CreateShortcut(Path.Combine(targetStartMenu, "Desinstalar Nexo.lnk"), uninstallPath, installDir, iconPath);
                } catch {}

                if (chkDesktop.Checked) {
                    string targetDesktop = allUsers ? commonDesktop : userDesktop;
                    if (!string.IsNullOrEmpty(targetDesktop)) {
                        CreateShortcut(Path.Combine(targetDesktop, "Nexo.lnk"), exePath, installDir, iconPath);
                    }
                }

                // Registro no Painel de Controle do Windows (Aplicativos Instalados)
                try {
                    using (RegistryKey baseKey = RegistryKey.OpenBaseKey(RegistryHive.LocalMachine, RegistryView.Registry64))
                    using (RegistryKey key = baseKey.CreateSubKey(@"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Nexo")) {
                        if (key != null) {
                            key.SetValue("DisplayName", "Nexo - Gestão de Custos e Precificação");
                            key.SetValue("DisplayVersion", "__VERSION__");
                            key.SetValue("Publisher", "Leonan Garcia");
                            key.SetValue("DisplayIcon", iconPath);
                            key.SetValue("InstallLocation", installDir);
                            key.SetValue("UninstallString", "\"" + uninstallPath + "\"");
                            key.SetValue("QuietUninstallString", "\"" + uninstallPath + "\"");
                            key.SetValue("NoModify", 1, RegistryValueKind.DWord);
                            key.SetValue("NoRepair", 1, RegistryValueKind.DWord);
                        }
                    }
                } catch {}

                progressBar.Value = 100;
                bool shouldLaunch = chkLaunch.Checked && File.Exists(exePath);
                MessageBox.Show(
                    "Instalação concluída com sucesso!",
                    "Nexo v__VERSION__",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                );

                this.Hide();
                Application.DoEvents();

                if (shouldLaunch) {
                    try {
                        ProcessStartInfo psi = new ProcessStartInfo("explorer.exe", "\"" + exePath + "\"");
                        psi.WorkingDirectory = installDir;
                        psi.UseShellExecute = false;
                        Process.Start(psi);
                    } catch {}
                }
                Environment.Exit(0);
            }
            catch (Exception ex) {
                MessageBox.Show("Erro durante a instalação:\n" + ex.Message, "Erro", MessageBoxButtons.OK, MessageBoxIcon.Error);
                btnInstall.Enabled = true;
                btnCancel.Enabled = true;
                btnBrowse.Enabled = true;
                txtInstallDir.Enabled = true;
                rbAllUsers.Enabled = true;
                rbCurrentUser.Enabled = true;
                chkDesktop.Enabled = true;
                chkLaunch.Enabled = true;
            }
        }

        private static void CreateShortcut(string shortcutPath, string targetPath, string workDir, string iconPath)
        {
            try {
                Type t = Type.GetTypeFromProgID("WScript.Shell");
                dynamic shell = Activator.CreateInstance(t);
                var lnk = shell.CreateShortcut(shortcutPath);
                lnk.TargetPath = targetPath;
                lnk.WorkingDirectory = workDir;
                if (File.Exists(iconPath)) {
                    lnk.IconLocation = iconPath;
                }
                lnk.Description = "Nexo - Gestão de Custos e Precificação";
                lnk.Save();
            } catch {}
        }

        [STAThread]
        public static void Main()
        {
            if (!IsAdmin()) {
                try {
                    ProcessStartInfo psi = new ProcessStartInfo(Application.ExecutablePath);
                    psi.Verb = "runas";
                    Process.Start(psi);
                } catch {
                    MessageBox.Show(
                        "A instalação do Nexo requer permissão de Administrador.",
                        "Nexo",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    );
                }
                return;
            }
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new SetupForm());
        }
    }
}
'''


def main():
    version = detect_version()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    build_work = ROOT_DIR / 'build' / 'pyinstaller_work'
    dist_dir = ROOT_DIR / 'build' / 'pyinstaller_dist'
    build_work.mkdir(parents=True, exist_ok=True)

    # Remove arquivo antigo sem sufixo _x64 se existir
    old_setup = OUTPUT_DIR / f'Nexo_Setup_v{version}.exe'
    if old_setup.exists():
        try:
            old_setup.unlink()
        except Exception:
            pass

    version_info_file = ROOT_DIR / 'build' / 'version_info.txt'
    version_info_file.write_text(make_pyinstaller_version_info(version), encoding='utf-8')

    frontend_dist = ROOT_DIR / 'frontend' / 'dist'
    if not (frontend_dist / 'index.html').exists():
        raise RuntimeError('Build do frontend não encontrado em frontend/dist. Execute "npm --prefix frontend run build" antes de empacotar.')

    print(f'=== 1. Empacotando Nexo v{version} (x64) com PyInstaller (banco zerado, sem dados de teste) ===')
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm', '--onedir', '--windowed',
        '--name', 'Nexo',
        '--icon', str(ROOT_DIR / 'nexo_icon.ico'),
        '--version-file', str(version_info_file),
        '--workpath', str(build_work),
        '--distpath', str(dist_dir),
        '--collect-submodules', 'backend',
        '--collect-submodules', 'webview',
        '--add-data', f'{frontend_dist};frontend/dist',
        '--add-data', f'{ROOT_DIR / "ui_assets"};ui_assets',
        '--add-data', f'{ROOT_DIR / "nexo_icon.ico"};.',
        '--add-data', f'{ROOT_DIR / "nexo_icon.png"};.',
        '--add-data', f'{ROOT_DIR / "nexo_logo.png"};.',
        str(ROOT_DIR / 'main.py'),
    ]

    subprocess.run(cmd, cwd=str(ROOT_DIR), check=True)

    app_bundle_dir = dist_dir / 'Nexo'
    for extra in ('nexo_icon.ico', 'nexo_icon.png', 'nexo_logo.png'):
        src = ROOT_DIR / extra
        if src.exists():
            shutil.copy2(src, app_bundle_dir / extra)

    # Trava de segurança: garante pacote 100% limpo para novo usuário (sem BD, chaves ou pastas pessoais)
    forbidden_names = {
        'nexo.db', 'nexo_config.json', 'nexo_file_config.json', '.env',
        'backups', 'documentos', 'documents', 'user_data',
    }
    leaks = [
        str(p.relative_to(app_bundle_dir))
        for p in app_bundle_dir.rglob('*')
        if p.name.lower() in forbidden_names or p.suffix.lower() in {'.db', '.sqlite', '.sqlite3'}
    ]
    if leaks:
        raise RuntimeError(
            'Build abortado! Arquivos pessoais/de desenvolvimento encontrados no bundle: '
            + ', '.join(leaks)
        )

    csc_candidates = list(Path(r'C:\Windows\Microsoft.NET\Framework64').glob('v4*/csc.exe'))
    if not csc_candidates:
        csc_candidates = list(Path(r'C:\Windows\Microsoft.NET\Framework').glob('v4*/csc.exe'))
    if not csc_candidates:
        raise RuntimeError('Compilador nativo do Windows (csc.exe) não encontrado.')
    csc_exe = csc_candidates[-1]

    manifest_file = ROOT_DIR / 'build' / 'setup.manifest'
    manifest_file.write_text(UAC_MANIFEST_XML, encoding='utf-8')

    print('=== 2. Compilando Desinstalador Oficial x64 (Uninstall_Nexo.exe) ===')
    uninst_cs = ROOT_DIR / 'build' / 'NexoUninstall.cs'
    uninst_cs.write_text(CSHARP_UNINSTALLER_TEMPLATE.replace('__VERSION__', version), encoding='utf-8-sig')
    uninst_exe = app_bundle_dir / 'Uninstall_Nexo.exe'
    subprocess.run([
        str(csc_exe),
        '/target:winexe',
        '/platform:x64',
        '/optimize+',
        f'/out:{uninst_exe}',
        f'/win32icon:{ROOT_DIR / "nexo_icon.ico"}',
        f'/win32manifest:{manifest_file}',
        '/reference:System.dll',
        '/reference:System.Drawing.dll',
        '/reference:System.Windows.Forms.dll',
        str(uninst_cs),
    ], cwd=str(ROOT_DIR), check=True)

    # Copia tambem o Uninstall_Nexo.exe para a pasta instaladores/ como ferramenta de seguranca
    shutil.copy2(uninst_exe, OUTPUT_DIR / 'Uninstall_Nexo.exe')

    print('=== 3. Compactando pacote de instalacao ===')
    payload_zip = ROOT_DIR / 'build' / 'payload.zip'
    if payload_zip.exists():
        payload_zip.unlink()
    with zipfile.ZipFile(payload_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for file_path in app_bundle_dir.rglob('*'):
            if file_path.is_file():
                rel = file_path.relative_to(app_bundle_dir)
                zf.write(file_path, rel.as_posix())

    print('=== 4. Compilando Instalador Windows x64 (Nexo_Setup_v' + version + '_x64.exe) ===')
    cs_file = ROOT_DIR / 'build' / 'NexoSetup.cs'
    cs_code = CSHARP_INSTALLER_TEMPLATE.replace('__VERSION__', version)
    cs_file.write_text(cs_code, encoding='utf-8-sig')

    setup_exe_path = OUTPUT_DIR / f'Nexo_Setup_v{version}_x64.exe'
    csc_cmd = [
        str(csc_exe),
        '/target:winexe',
        '/platform:x64',
        '/optimize+',
        f'/out:{setup_exe_path}',
        f'/win32icon:{ROOT_DIR / "nexo_icon.ico"}',
        f'/win32manifest:{manifest_file}',
        f'/resource:{payload_zip},payload.zip',
        f'/resource:{ROOT_DIR / "ui_assets" / "nexo_about_light.png"},nexo_about_light.png',
        '/reference:System.dll',
        '/reference:System.Drawing.dll',
        '/reference:System.Windows.Forms.dll',
        '/reference:System.IO.Compression.dll',
        '/reference:System.IO.Compression.FileSystem.dll',
        '/reference:Microsoft.CSharp.dll',
        str(cs_file),
    ]
    subprocess.run(csc_cmd, cwd=str(ROOT_DIR), check=True)
    shutil.rmtree(ROOT_DIR / 'build', ignore_errors=True)
    spec_file = ROOT_DIR / 'Nexo.spec'
    if spec_file.exists():
        spec_file.unlink()
    print(f'\n[SUCESSO] Instalador x64 gerado em: {setup_exe_path}')
    print(f'[SUCESSO] Desinstalador gerado em: {OUTPUT_DIR / "Uninstall_Nexo.exe"}')


if __name__ == '__main__':
    main()
