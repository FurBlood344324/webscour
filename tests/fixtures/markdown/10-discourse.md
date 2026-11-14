# Code, which operates outside of a notebook, fails when invoked within it

**beedell.roke**

I am attempting to trial using a Jupyter Notebook to make some repetitive processes more convenient to conduct. However, as the undermentioned IPython Notebook source demonstrates, this has been unsuccessful:

```JSON
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "804bc4c5",
   "metadata": {
    "vscode": {
     "languageId": "powershell"
    }
   },
   "outputs": [
    {
     "ename": "SyntaxError",
     "evalue": "invalid decimal literal (93048999.py, line 9)",
     "output_type": "error",
     "traceback": [
      "  \u001b[36mCell\u001b[39m\u001b[36m \u001b[39m\u001b[32mIn[1]\u001b[39m\u001b[32m, line 9\u001b[39m\n\u001b[31m    \u001b[39m\u001b[31m$Int64 = 0L\u001b[39m\n             ^\n\u001b[31mSyntaxError\u001b[39m\u001b[31m:\u001b[39m invalid decimal literal\n"
     ]
    }
   ],
   "source": [
    "#!/usr/bin/env -S pwsh -File\n",
    "$Object = [Ordered]@{}\n",
    "@(\n",
    "\t'ro.product.brand'\n",
    "\t'ro.build.product'\n",
    ") | ForEach-Object {\n",
    "\t$Value = (adb shell \"getprop $_\").Trim()\n",
    "\tIf ($Value) {\n",
    "\t\t$Int64 = 0L\n",
    "\t\t$Object[$_] =\n",
    "\t\t\tIf ([Long]::TryParse($Value, [Ref]$Int64)) {\n",
    "\t\t\t\t$Int64\n",
    "\t\t\t} Else {\n",
    "\t\t\t\t$Value\n",
    "\t\t\t}\n",
    "\t}\n",
    "}\n",
    "$Object |\n",
    "\tConvertTo-Json -Compress |\n",
    "\tyq -P"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 3,
   "id": "9910da30",
   "metadata": {
    "vscode": {
     "languageId": "powershell"
    }
   },
   "outputs": [
    {
     "ename": "SyntaxError",
     "evalue": "invalid decimal literal (830812845.py, line 11)",
     "output_type": "error",
     "traceback": [
      "  \u001b[36mCell\u001b[39m\u001b[36m \u001b[39m\u001b[32mIn[3]\u001b[39m\u001b[32m, line 11\u001b[39m\n\u001b[31m    \u001b[39m\u001b[31m$Int64 = 0L\u001b[39m\n             ^\n\u001b[31mSyntaxError\u001b[39m\u001b[31m:\u001b[39m invalid decimal literal\n"
     ]
    }
   ],
   "source": [
    "#!/usr/bin/env -S pwsh -File\n",
    "$Object = [Ordered]@{}\n",
    "@(\n",
    "\t'ro.build.display.id'\n",
    "\t'ro.build.fingerprint'\n",
    "\t'ro.build.version.sdk'\n",
    "\t'ro.build.version.sdk_full'\n",
    ") | ForEach-Object {\n",
    "\t$Value = (adb shell \"getprop $_\").Trim()\n",
    "\tIf ($Value) {\n",
    "\t\t$Int64 = 0L\n",
    "\t\t$Object[$_] =\n",
    "\t\t\tIf ([Long]::TryParse($Value, [Ref]$Int64)) {\n",
    "\t\t\t\t$Int64\n",
    "\t\t\t} Else {\n",
    "\t\t\t\t$Value\n",
    "\t\t\t}\n",
    "\t}\n",
    "}\n",
    "$Object |\n",
    "\tConvertTo-Json -Compress |\n",
    "\tyq -P"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 2,
   "id": "5abdb8a8",
   "metadata": {
    "vscode": {
     "languageId": "powershell"
    }
   },
   "outputs": [
    {
     "ename": "SyntaxError",
     "evalue": "invalid decimal literal (3797982989.py, line 16)",
     "output_type": "error",
     "traceback": [
      "  \u001b[36mCell\u001b[39m\u001b[36m \u001b[39m\u001b[32mIn[2]\u001b[39m\u001b[32m, line 16\u001b[39m\n\u001b[31m    \u001b[39m\u001b[31m$Int64 = 0L\u001b[39m\n             ^\n\u001b[31mSyntaxError\u001b[39m\u001b[31m:\u001b[39m invalid decimal literal\n"
     ]
    }
   ],
   "source": [
    "#!/usr/bin/env -S pwsh -File\n",
    "$Package = Read-Host\n",
    "$DumpSys = adb shell \"dumpsys package $Package\"\n",
    "$Object = [Ordered]@{}\n",
    "@{\n",
    "\tversionCode = 'versionCode=(\\d+)'\n",
    "\tversionName = 'versionName=([^\\s]+)'\n",
    "}.GetEnumerator() | ForEach-Object {\n",
    "\t$Match = [RegEx]::Match(\n",
    "\t\t$DumpSys,\n",
    "\t\t$_.Value,\n",
    "\t\t[System.Text.RegularExpressions.RegexOptions]::Multiline\n",
    "\t)\n",
    "\tIf ($Match.Success) {\n",
    "\t\t$Value = $Match.Groups[1].Value\n",
    "\t\t$Int64 = 0L\n",
    "\t\t$Object[$_.Key] =\n",
    "\t\t\tIf ([Long]::TryParse($Value, [Ref]$Int64)) {\n",
    "\t\t\t\t$Int64\n",
    "\t\t\t} Else {\n",
    "\t\t\t\t$Value\n",
    "\t\t\t}\n",
    "\t}\n",
    "}\n",
    "$Object.installer = (\n",
    "\tadb shell 'pm list packages -i' |\n",
    "\t\tSelect-String \"^package:$([RegEx]::Escape($Package)) \" |\n",
    "\t\tForEach-Object {\n",
    "\t\t\t$_ -replace '^.*installer='\n",
    "\t\t}\n",
    ")\n",
    "$Object |\n",
    "\tConvertTo-JSON -Compress |\n",
    "\tyq -P"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.15.2"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
```

However, what is strange about this example is that each of those commands functions perfectly outside of the notebook:

Why might this be so?

My environment is as ``[`stackoverflow.com/revisions/80016499/2`](https://stackoverflow.com/revisions/80016499/2#content:~:text=In%20cPE,pip,-My)`` describes:

- ```YAML
  Name: python3.15
  Version: 3.15.2
  Release: 1.fc44
  Buildtime: 1793096508
  Buildhost: buildhw-x86-16.rdu3.fedoraproject.org
  Installtime: 1793884028
  Size: 29310
  Distribution: Fedora Project
  Vendor: Fedora Project
  License: Python-2.0.1
  Packager: Fedora Project
  ```
-

I invoke it via:

BTW, that proposed correction is incorrect.

**fomightez**

So the screenshot you show at the bottom has in the upper right the kernel you are using as ‘`Python 3.15.2`’, I think. (I only ever use actual Jupyter that show ipkernel so I am guessing a bit there, but what I see for the errors is consistent.)
However, that code in the cell isn’t Python. So it won’t work and is saying `SyntaxError: invalid decimal literal`, etc.. From the text of what you provided as your notebook in the code block at the tiop, from the medata it looks like you’d want `"languageId": "powershell"`. I don’t know if that is a common kernel. I have used the Bash kernel. And more often than not, it is easier to run bash commands in ipykernel notebooks with the `%%bash` cell magic (see [here](https://ipython.readthedocs.io/en/stable/interactive/magics.html#cellmagic-bash)) or subprocess. I don’t use powershell at all so I cannot tell you if there is an equivalent. I think you can to some extent because of the answer to [Executing Windows PowerShell commands in a Jupyter Notebook](https://stackoverflow.com/a/70604096/8508004).

See also:

**beedell.roke**

[@fomightez](https://discourse.jupyter.org/u/fomightez), indeed. That appears to be problem:

I have, since, solved it, with `%%script powershell-preview -NoProfile -NonInteractive -Command "& ([scriptblock]::Create([Console]::In.ReadToEnd()))"` prepended.

```JSON
{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": 24,
   "id": "804bc4c5",
   "metadata": {
    "vscode": {
     "languageId": "powershell"
    }
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "ro.product.brand: Fairphone\n",
      "ro.build.product: FP5\n"
     ]
    }
   ],
   "source": [
    "%%script powershell-preview -NoProfile -NonInteractive -Command \"& ([scriptblock]::Create([Console]::In.ReadToEnd()))\"\n",
    "#!/usr/bin/env -S powershell-preview -File\n",
    "$Object = [Ordered]@{}\n",
    "@(\n",
    "\t'ro.product.brand'\n",
    "\t'ro.build.product'\n",
    ") | ForEach-Object {\n",
    "\t$Value = (adb shell \"getprop $_\").Trim()\n",
    "\tIf ($Value) {\n",
    "\t\t$Int64 = 0L\n",
    "\t\t$Object[$_] =\n",
    "\t\t\tIf ([Long]::TryParse($Value, [Ref]$Int64)) {\n",
    "\t\t\t\t$Int64\n",
    "\t\t\t} Else {\n",
    "\t\t\t\t$Value\n",
    "\t\t\t}\n",
    "\t}\n",
    "}\n",
    "$Object |\n",
    "\tConvertTo-Json -Compress |\n",
    "\tyq -P\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "9910da30",
   "metadata": {
    "vscode": {
     "languageId": "powershell"
    }
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "ro.build.display.id: FP5.VT32.C.116.20260903\n",
      "ro.build.fingerprint: Fairphone/FP5/FP5:15/AQ3A.240912.001/VT32:user/release-keys\n",
      "ro.build.version.sdk: 35\n"
     ]
    }
   ],
   "source": [
    "%%script powershell-preview -NoProfile -NonInteractive -Command \"& ([scriptblock]::Create([Console]::In.ReadToEnd()))\"\n",
    "#!/usr/bin/env -S powershell-preview -File\n",
    "$Object = [Ordered]@{}\n",
    "@(\n",
    "\t'ro.build.display.id'\n",
    "\t'ro.build.fingerprint'\n",
    "\t'ro.build.version.sdk'\n",
    "\t'ro.build.version.sdk_full'\n",
    ") | ForEach-Object {\n",
    "\t$Value = (adb shell \"getprop $_\").Trim()\n",
    "\tIf ($Value) {\n",
    "\t\t$Int64 = 0L\n",
    "\t\t$Object[$_] =\n",
    "\t\t\tIf ([Long]::TryParse($Value, [Ref]$Int64)) {\n",
    "\t\t\t\t$Int64\n",
    "\t\t\t} Else {\n",
    "\t\t\t\t$Value\n",
    "\t\t\t}\n",
    "\t}\n",
    "}\n",
    "$Object |\n",
    "\tConvertTo-Json -Compress |\n",
    "\tyq -P\n"
   ]
  },
  {
   "cell_type": "code",
   "execution_count": 1,
   "id": "5abdb8a8",
   "metadata": {
    "vscode": {
     "languageId": "powershell"
    }
   },
   "outputs": [
    {
     "name": "stdout",
     "output_type": "stream",
     "text": [
      "versionName: 15\n",
      "versionCode: 35\n",
      "installer: \"null\"\n"
     ]
    }
   ],
   "source": [
    "%%script powershell-preview -NoProfile -NonInteractive -Command \"& ([scriptblock]::Create([Console]::In.ReadToEnd()))\"\n",
    "#!/usr/bin/env -S powershell-preview -File\n",
    "$Package = \"com.android.settings\"\n",
    "$DumpSys = adb shell \"dumpsys package $Package\"\n",
    "$Object = [Ordered]@{}\n",
    "@{\n",
    "\tversionCode = 'versionCode=(\\d+)'\n",
    "\tversionName = 'versionName=([^\\s]+)'\n",
    "}.GetEnumerator() | ForEach-Object {\n",
    "\t$Match = [RegEx]::Match(\n",
    "\t\t$DumpSys,\n",
    "\t\t$_.Value,\n",
    "\t\t[System.Text.RegularExpressions.RegexOptions]::Multiline\n",
    "\t)\n",
    "\tIf ($Match.Success) {\n",
    "\t\t$Value = $Match.Groups[1].Value\n",
    "\t\t$Int64 = 0L\n",
    "\t\t$Object[$_.Key] =\n",
    "\t\t\tIf ([Long]::TryParse($Value, [Ref]$Int64)) {\n",
    "\t\t\t\t$Int64\n",
    "\t\t\t} Else {\n",
    "\t\t\t\t$Value\n",
    "\t\t\t}\n",
    "\t}\n",
    "}\n",
    "$Object.installer = (\n",
    "\tadb shell 'pm list packages -i' |\n",
    "\t\tSelect-String \"^package:$([RegEx]::Escape($Package)) \" |\n",
    "\t\tForEach-Object {\n",
    "\t\t\t$_ -replace '^.*installer='\n",
    "\t\t}\n",
    ")\n",
    "$Object |\n",
    "\tConvertTo-JSON -Compress |\n",
    "\tyq -P\n"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.15.2"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
```

To demonstrate:

This may have been multiple problems compounded:
