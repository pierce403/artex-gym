# Precious (HTB machine 513)

- **Difficulty** 35 (Easy), Linux
- **Started** 2026-11-26T17:13:51Z, IP `10.129.228.98`
- **ArTeX task** 55
- **User flag** `30b7628bf2f8f05f242637a44243f4dd` — accepted
- **Root flag** `fcb81029ffd5aef0a097d7287df0352a` — accepted
- **Outcome** solved

## Captured

- Blob run `20261126T024001Z-8b01caa6` — 151 blobs referencing `10.129.228.98`
- ArTeX task `55`; collector `dropped=0` for the run
- Findings:

  - **critical** — The Sinatra 'Convert Web Page to PDF' app at http://precious.htb/ passes the user-supplied url parameter unescaped into the wkhtmltopdf shell command
  - **high** — User henry may run `sudo /usr/bin/ruby /opt/update_dependencies.rb` without a password. The script calls YAML.load(File.read("dependencies.yml")) on a
