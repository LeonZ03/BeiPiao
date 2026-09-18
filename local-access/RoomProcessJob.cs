using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

// Only the server and tunnel join this job. The browser stays outside it.
// Windows closes the job handle even when its PowerShell owner is killed.
public sealed class RoomProcessJob : IDisposable
{
    private IntPtr job;

    public RoomProcessJob()
    {
        job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero) throw new Win32Exception();
        var limits = new ExtendedLimits();
        limits.BasicLimitInformation.LimitFlags = 0x2000; // KILL_ON_JOB_CLOSE
        if (!SetInformationJobObject(job, 9, ref limits, (uint)Marshal.SizeOf(limits)))
        {
            int error = Marshal.GetLastWin32Error();
            Dispose();
            throw new Win32Exception(error);
        }
    }

    public Process Start(string executable, string[] arguments, string directory,
                         string outputFile, string errorFile)
    {
        if (job == IntPtr.Zero) throw new ObjectDisposedException("RoomProcessJob");
        IntPtr output = IntPtr.Zero, error = IntPtr.Zero, input = IntPtr.Zero;
        var process = new ProcessInformation();
        bool started = false;
        try
        {
            output = OpenInheritableFile(outputFile, 0x40000000, 2);
            error = OpenInheritableFile(errorFile, 0x40000000, 2);
            input = OpenInheritableFile("NUL", 0x80000000, 3);
            var startup = new StartupInfo();
            startup.cb = Marshal.SizeOf(startup);
            startup.dwFlags = 0x100; // STARTF_USESTDHANDLES
            startup.hStdOutput = output;
            startup.hStdError = error;
            startup.hStdInput = input;
            var command = new StringBuilder(Quote(executable));
            foreach (string argument in arguments) command.Append(' ').Append(Quote(argument));
            // Suspend first: no child can escape between launch and job assignment.
            if (!CreateProcess(executable, command, IntPtr.Zero, IntPtr.Zero, true,
                               0x08000004, IntPtr.Zero, directory, ref startup, out process))
                throw new Win32Exception();
            started = true;
            if (!AssignProcessToJobObject(job, process.hProcess)) throw new Win32Exception();
            var result = Process.GetProcessById((int)process.dwProcessId);
            if (ResumeThread(process.hThread) == uint.MaxValue) throw new Win32Exception();
            return result;
        }
        catch
        {
            if (started) TerminateProcess(process.hProcess, 1);
            throw;
        }
        finally
        {
            CloseIfValid(process.hThread);
            CloseIfValid(process.hProcess);
            CloseIfValid(input);
            CloseIfValid(error);
            CloseIfValid(output);
        }
    }

    private static IntPtr OpenInheritableFile(string path, uint access, uint disposition)
    {
        var security = new SecurityAttributes();
        security.nLength = Marshal.SizeOf(security);
        security.bInheritHandle = true;
        IntPtr file = CreateFile(path, access, 3, ref security, disposition, 0x80, IntPtr.Zero);
        if (file == new IntPtr(-1)) throw new Win32Exception();
        return file;
    }

    private static string Quote(string value)
    {
        var quoted = new StringBuilder("\"");
        int slashes = 0;
        foreach (char c in value)
        {
            if (c == '\\') { slashes++; continue; }
            quoted.Append('\\', c == '"' ? slashes * 2 + 1 : slashes);
            quoted.Append(c);
            slashes = 0;
        }
        quoted.Append('\\', slashes * 2).Append('"');
        return quoted.ToString();
    }

    private static void CloseIfValid(IntPtr handle)
    {
        if (handle != IntPtr.Zero && handle != new IntPtr(-1)) CloseHandle(handle);
    }

    public void Dispose()
    {
        if (job != IntPtr.Zero) { CloseHandle(job); job = IntPtr.Zero; }
        GC.SuppressFinalize(this);
    }

    ~RoomProcessJob() { Dispose(); }

    [StructLayout(LayoutKind.Sequential)]
    private struct BasicLimits
    {
        public long PerProcessUserTimeLimit, PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize, MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass, SchedulingClass;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct IoCounters
    {
        public ulong ReadOperationCount, WriteOperationCount, OtherOperationCount;
        public ulong ReadTransferCount, WriteTransferCount, OtherTransferCount;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct ExtendedLimits
    {
        public BasicLimits BasicLimitInformation;
        public IoCounters IoInfo;
        public UIntPtr ProcessMemoryLimit, JobMemoryLimit, PeakProcessMemoryUsed, PeakJobMemoryUsed;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct SecurityAttributes
    {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        [MarshalAs(UnmanagedType.Bool)] public bool bInheritHandle;
    }
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct StartupInfo
    {
        public int cb;
        public string lpReserved, lpDesktop, lpTitle;
        public uint dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
        public ushort wShowWindow, cbReserved2;
        public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct ProcessInformation
    {
        public IntPtr hProcess, hThread;
        public uint dwProcessId, dwThreadId;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetInformationJobObject(IntPtr job, int infoClass, ref ExtendedLimits info, uint length);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CreateProcess(string app, StringBuilder command, IntPtr processAttributes,
        IntPtr threadAttributes, bool inheritHandles, uint flags, IntPtr environment,
        string directory, ref StartupInfo startup, out ProcessInformation process);
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CreateFile(string path, uint access, uint share,
        ref SecurityAttributes security, uint disposition, uint attributes, IntPtr template);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool TerminateProcess(IntPtr process, uint exitCode);
    [DllImport("kernel32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(IntPtr handle);
}
