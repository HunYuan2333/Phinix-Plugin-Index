#!/usr/bin/env python3
"""Compile a local static validator from explicitly trusted working trees; never change production provenance."""
import argparse,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--client-root',type=Path,required=True);p.add_argument('--common-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[1];out=a.output.resolve()
for protected in [root,a.client_root.resolve(),a.common_root.resolve()]:
 if out.is_relative_to(protected) or protected.is_relative_to(out):p.error('Use a fresh output outside source trees.')
if out.exists() and any(out.iterdir()):p.error('Output already exists.')
out.mkdir(parents=True,exist_ok=True);manifest=json.loads((root/'Validator/production-provenance.json').read_text());files=[]
for record in manifest['files']:
 base=a.common_root if record['origin']=='common' else a.client_root;files.append((base/record['source']).resolve())
files.append((a.common_root/'Common/Utils/Framework/ManagedExtensions/ManagedExtensionZip.cs').resolve())
files+=list((root/'Validator').glob('*.cs'))
for path in files:
 if not path.is_file():p.error('Missing trusted source: '+str(path))
project=ET.Element('Project',Sdk='Microsoft.NET.Sdk');pg=ET.SubElement(project,'PropertyGroup')
for key,value in {'TargetFramework':'net10.0','OutputType':'Exe','AssemblyName':'Validator','EnableDefaultCompileItems':'false','NuGetAudit':'false'}.items():ET.SubElement(pg,key).text=value
items=ET.SubElement(project,'ItemGroup')
for path in sorted(set(files)):ET.SubElement(items,'Compile',Include=str(path))
ET.ElementTree(project).write(out/'Validator.csproj',encoding='unicode');(out/'NuGet.Config').write_text('<configuration><packageSources><clear /></packageSources></configuration>')
subprocess.run(['dotnet','build',str(out/'Validator.csproj'),'-c','Release','-v:q'],check=True)
(out/'LOCAL-SCOPE.txt').write_text('Development validation only. Production origins and frozen snapshots were not changed; refresh them from final matching committed client/common sources before deployment.\n')
print(out/'bin/Release/net10.0/Validator.dll')
