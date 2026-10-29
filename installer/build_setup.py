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
    app_file = ROOT_DIR / 'frontend' / 'app.py'
    if app_file.exists():
        m = re.search(r'v(\d+\.\d+\.\d+)', app_file.read_text(encoding='utf-8'))
        if m:
            return m.group(1)
    main_file = ROOT_DIR / 'main.py'
    if main_file.exists():
        m = re.search(r'v(\d+\.\d+\.\d+)', main_file.read_text(encoding='utf-8'))
        if m:
            return m.group(1)
    return '1.0.0'


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
    public class UninstallForm : Form
    {
        private Label titleLabel;
        private Label subLabel;
        private Label statusLabel;
        private CheckBox chkRemoveData;
        private ProgressBar progressBar;
        private Button btnUninstall;
        private Button btnCancel;

        private string originInstallDir;

        public UninstallForm(string originDir)
        {
            this.originInstallDir = originDir;
            this.Text = "Desinstalar Nexo v__VERSION__";
            this.Size = new Size(520, 310);
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
            header.Height = 78;
            header.BackColor = Color.FromArgb(17, 28, 48);

            titleLabel = new Label();
            titleLabel.Text = "Desinstalar Nexo v__VERSION__";
            titleLabel.ForeColor = Color.White;
            titleLabel.Font = new Font("Segoe UI", 16F, FontStyle.Bold);
            titleLabel.Location = new Point(24, 14);
            titleLabel.AutoSize = true;
            header.Controls.Add(titleLabel);

            subLabel = new Label();
            subLabel.Text = "Gestão de Custos, Ficha Técnica e Precificação";
            subLabel.ForeColor = Color.FromArgb(242, 140, 40);
            subLabel.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            subLabel.Location = new Point(26, 46);
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

            progressBar = new ProgressBar();
            progressBar.Location = new Point(26, 172);
            progressBar.Size = new Size(452, 22);
            progressBar.Style = ProgressBarStyle.Continuous;
            this.Controls.Add(progressBar);

            btnUninstall = new Button();
            btnUninstall.Text = "Desinstalar";
            btnUninstall.BackColor = Color.FromArgb(217, 75, 61);
            btnUninstall.ForeColor = Color.White;
            btnUninstall.FlatStyle = FlatStyle.Flat;
            btnUninstall.FlatAppearance.BorderSize = 0;
            btnUninstall.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
            btnUninstall.Location = new Point(338, 214);
            btnUninstall.Size = new Size(140, 36);
            btnUninstall.Cursor = Cursors.Hand;
            btnUninstall.Click += BtnUninstall_Click;
            this.Controls.Add(btnUninstall);

            btnCancel = new Button();
            btnCancel.Text = "Cancelar";
            btnCancel.BackColor = Color.FromArgb(226, 232, 240);
            btnCancel.ForeColor = Color.FromArgb(24, 34, 58);
            btnCancel.FlatStyle = FlatStyle.Flat;
            btnCancel.FlatAppearance.BorderSize = 0;
            btnCancel.Location = new Point(228, 214);
            btnCancel.Size = new Size(100, 36);
            btnCancel.Cursor = Cursors.Hand;
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
    public class SetupForm : Form
    {
        private Label titleLabel;
        private Label subLabel;
        private Label dirTitleLabel;
        private TextBox txtInstallDir;
        private Button btnBrowse;
        private Label scopeTitleLabel;
        private RadioButton rbAllUsers;
        private RadioButton rbCurrentUser;
        private Label optTitleLabel;
        private CheckBox chkDesktop;
        private CheckBox chkLaunch;
        private ProgressBar progressBar;
        private Button btnInstall;
        private Button btnCancel;

        public static string GetDefaultProgramFilesDir()
        {
            string pf64 = Environment.GetEnvironmentVariable("ProgramW6432");
            if (!string.IsNullOrEmpty(pf64) && Directory.Exists(pf64)) {
                return Path.Combine(pf64, "Nexo");
            }
            return Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "Nexo");
        }

        public SetupForm()
        {
            this.Text = "Instalador do Nexo v__VERSION__ (x64)";
            this.Size = new Size(540, 420);
            this.FormBorderStyle = FormBorderStyle.FixedDialog;
            this.MaximizeBox = false;
            this.StartPosition = FormStartPosition.CenterScreen;
            this.BackColor = Color.FromArgb(244, 247, 252);
            this.Font = new Font("Segoe UI", 9.5F);

            try {
                this.Icon = Icon.ExtractAssociatedIcon(Application.ExecutablePath);
            } catch {}

            Panel header = new Panel();
            header.Dock = DockStyle.Top;
            header.Height = 80;
            header.BackColor = Color.FromArgb(17, 28, 48);

            titleLabel = new Label();
            titleLabel.Text = "Nexo v__VERSION__";
            titleLabel.ForeColor = Color.White;
            titleLabel.Font = new Font("Segoe UI", 18F, FontStyle.Bold);
            titleLabel.Location = new Point(24, 12);
            titleLabel.AutoSize = true;
            header.Controls.Add(titleLabel);

            subLabel = new Label();
            subLabel.Text = "Gestão de Custos, Ficha Técnica e Precificação";
            subLabel.ForeColor = Color.FromArgb(242, 140, 40);
            subLabel.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
            subLabel.Location = new Point(26, 46);
            subLabel.AutoSize = true;
            header.Controls.Add(subLabel);

            this.Controls.Add(header);

            dirTitleLabel = new Label();
            dirTitleLabel.Text = "Pasta de instalação:";
            dirTitleLabel.ForeColor = Color.FromArgb(24, 34, 58);
            dirTitleLabel.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            dirTitleLabel.Location = new Point(26, 96);
            dirTitleLabel.AutoSize = true;
            this.Controls.Add(dirTitleLabel);

            txtInstallDir = new TextBox();
            txtInstallDir.Text = GetDefaultProgramFilesDir();
            txtInstallDir.Location = new Point(26, 118);
            txtInstallDir.Size = new Size(360, 26);
            txtInstallDir.Font = new Font("Segoe UI", 9.5F);
            this.Controls.Add(txtInstallDir);

            btnBrowse = new Button();
            btnBrowse.Text = "Procurar...";
            btnBrowse.BackColor = Color.FromArgb(226, 232, 240);
            btnBrowse.ForeColor = Color.FromArgb(24, 34, 58);
            btnBrowse.FlatStyle = FlatStyle.Flat;
            btnBrowse.FlatAppearance.BorderSize = 0;
            btnBrowse.Location = new Point(394, 116);
            btnBrowse.Size = new Size(104, 28);
            btnBrowse.Cursor = Cursors.Hand;
            btnBrowse.Click += BtnBrowse_Click;
            this.Controls.Add(btnBrowse);

            scopeTitleLabel = new Label();
            scopeTitleLabel.Text = "Opções de acesso:";
            scopeTitleLabel.ForeColor = Color.FromArgb(24, 34, 58);
            scopeTitleLabel.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            scopeTitleLabel.Location = new Point(26, 156);
            scopeTitleLabel.AutoSize = true;
            this.Controls.Add(scopeTitleLabel);

            rbAllUsers = new RadioButton();
            rbAllUsers.Text = "Todos os usuários (Padrão)";
            rbAllUsers.Checked = true;
            rbAllUsers.ForeColor = Color.FromArgb(24, 34, 58);
            rbAllUsers.Location = new Point(28, 178);
            rbAllUsers.AutoSize = true;
            this.Controls.Add(rbAllUsers);

            rbCurrentUser = new RadioButton();
            rbCurrentUser.Text = "Apenas para mim";
            rbCurrentUser.Checked = false;
            rbCurrentUser.ForeColor = Color.FromArgb(24, 34, 58);
            rbCurrentUser.Location = new Point(260, 178);
            rbCurrentUser.AutoSize = true;
            this.Controls.Add(rbCurrentUser);

            optTitleLabel = new Label();
            optTitleLabel.Text = "Opções extras:";
            optTitleLabel.ForeColor = Color.FromArgb(24, 34, 58);
            optTitleLabel.Font = new Font("Segoe UI", 9.5F, FontStyle.Bold);
            optTitleLabel.Location = new Point(26, 212);
            optTitleLabel.AutoSize = true;
            this.Controls.Add(optTitleLabel);

            chkDesktop = new CheckBox();
            chkDesktop.Text = "Criar atalho na Área de Trabalho";
            chkDesktop.Checked = true;
            chkDesktop.ForeColor = Color.FromArgb(24, 34, 58);
            chkDesktop.Location = new Point(28, 234);
            chkDesktop.AutoSize = true;
            this.Controls.Add(chkDesktop);

            chkLaunch = new CheckBox();
            chkLaunch.Text = "Abrir o Nexo ao finalizar";
            chkLaunch.Checked = true;
            chkLaunch.ForeColor = Color.FromArgb(24, 34, 58);
            chkLaunch.Location = new Point(28, 260);
            chkLaunch.AutoSize = true;
            this.Controls.Add(chkLaunch);

            progressBar = new ProgressBar();
            progressBar.Location = new Point(26, 294);
            progressBar.Size = new Size(472, 20);
            progressBar.Style = ProgressBarStyle.Continuous;
            this.Controls.Add(progressBar);

            btnInstall = new Button();
            btnInstall.Text = "Instalar";
            btnInstall.BackColor = Color.FromArgb(242, 140, 40);
            btnInstall.ForeColor = Color.White;
            btnInstall.FlatStyle = FlatStyle.Flat;
            btnInstall.FlatAppearance.BorderSize = 0;
            btnInstall.Font = new Font("Segoe UI", 10F, FontStyle.Bold);
            btnInstall.Location = new Point(358, 328);
            btnInstall.Size = new Size(140, 36);
            btnInstall.Cursor = Cursors.Hand;
            btnInstall.Click += BtnInstall_Click;
            this.Controls.Add(btnInstall);

            btnCancel = new Button();
            btnCancel.Text = "Cancelar";
            btnCancel.BackColor = Color.FromArgb(226, 232, 240);
            btnCancel.ForeColor = Color.FromArgb(24, 34, 58);
            btnCancel.FlatStyle = FlatStyle.Flat;
            btnCancel.FlatAppearance.BorderSize = 0;
            btnCancel.Location = new Point(248, 328);
            btnCancel.Size = new Size(100, 36);
            btnCancel.Cursor = Cursors.Hand;
            btnCancel.Click += (s, e) => this.Close();
            this.Controls.Add(btnCancel);
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
            btnCancel.Enabled = false;
            btnBrowse.Enabled = false;
            txtInstallDir.Enabled = false;
            rbAllUsers.Enabled = false;
            rbCurrentUser.Enabled = false;
            chkDesktop.Enabled = false;
            chkLaunch.Enabled = false;
            progressBar.Value = 20;

            bool allUsers = rbAllUsers.Checked;

            try {
                await Task.Run(() => {
                    foreach (Process proc in Process.GetProcessesByName("Nexo")) {
                        try { proc.Kill(); proc.WaitForExit(2000); } catch {}
                    }
                    if (Directory.Exists(installDir)) {
                        try { Directory.Delete(installDir, true); } catch {}
                    }
                    Directory.CreateDirectory(installDir);

                    string userDataDir = Path.Combine(
                        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                        "Nexo"
                    );
                    Directory.CreateDirectory(userDataDir);
                    Directory.CreateDirectory(Path.Combine(userDataDir, "backups"));
                    Directory.CreateDirectory(Path.Combine(userDataDir, "documentos"));

                    Assembly asm = Assembly.GetExecutingAssembly();
                    using (Stream s = asm.GetManifestResourceStream("payload.zip")) {
                        string tempZip = Path.Combine(Path.GetTempPath(), "nexo_payload_" + Guid.NewGuid().ToString("N") + ".zip");
                        using (FileStream fs = new FileStream(tempZip, FileMode.Create, FileAccess.Write)) {
                            s.CopyTo(fs);
                        }
                        ZipFile.ExtractToDirectory(tempZip, installDir);
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

    print(f'=== 1. Empacotando Nexo v{version} (x64) com PyInstaller ===')
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        '--noconfirm', '--onedir', '--windowed',
        '--name', 'Nexo',
        '--icon', str(ROOT_DIR / 'nexo_icon.ico'),
        '--version-file', str(version_info_file),
        '--workpath', str(build_work),
        '--distpath', str(dist_dir),
        '--collect-submodules', 'backend',
        '--collect-submodules', 'frontend',
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
