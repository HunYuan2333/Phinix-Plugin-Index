using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Text;
using System.Runtime.Serialization.Json;
using System.Xml.Linq;
using System.Threading;
using Phinix.PluginStore;
using Utils.Framework.Themes;

internal static class ThemeValidation
{
    internal static byte[] Json(XElement node,bool sorted=false)
    {
        var copy=new XElement(node);copy.Name="root";
        if(sorted) Sort(copy);
        using(var output=new MemoryStream()) {using(var writer=JsonReaderWriterFactory.CreateJsonWriter(output,Encoding.UTF8,false)) copy.WriteTo(writer);return output.ToArray();}
    }
    private static void Sort(XElement node)
    {foreach(var child in node.Elements()) Sort(child);if((string)node.Attribute("type")=="object") node.ReplaceNodes(node.Elements().OrderBy(n=>n.Name.LocalName,StringComparer.Ordinal).ToArray());}
    internal static int Run(string[] args)
    {
        var f=CatalogReader.Object(CatalogReader.ReadJson(File.ReadAllBytes(args[2])),"themes","schemaVersion","sourceId","snapshotId","packages");
        CatalogReader.Integer(CatalogReader.Required(f,"schemaVersion"),"schemaVersion",4,4);
        if(CatalogReader.Identifier(CatalogReader.Required(f,"sourceId"),"sourceId")!=args[1]) throw new InvalidOperationException("SourceMismatch");
        CatalogReader.Hex(CatalogReader.Required(f,"snapshotId"),"snapshotId",40);
        var seen=new HashSet<string>(StringComparer.Ordinal);bool verified=false;
        foreach(var node in CatalogReader.Array(CatalogReader.Required(f,"packages"),"packages",256))
        {
            var p=CatalogReader.Object(node,"theme","id","state","management","channel","manifest","artifact","summary","license");
            string id=CatalogReader.Identifier(CatalogReader.Required(p,"id"),"id");
            if(CatalogReader.Text(CatalogReader.Required(p,"management"),"management",32)!="phinix-theme" || CatalogReader.Text(CatalogReader.Required(p,"channel"),"channel",32)!="github-release") throw new InvalidOperationException("UnsupportedManagement");
            string state=CatalogReader.Choice(CatalogReader.Required(p,"state"),"state","active","withdrawn","unmaintained");
            CatalogReader.Text(CatalogReader.Required(p,"summary"),"summary",1024);CatalogReader.Text(CatalogReader.Required(p,"license"),"license",128);
            var declared=CatalogReader.Required(p,"manifest");var manifest=ThemePackageManifest.Read(Json(declared));
            if(id!=manifest.PackageId || !seen.Add(id+"@"+manifest.Version)) throw new InvalidOperationException("ThemeIdentityMismatch");
            var artifactNode=new XElement(CatalogReader.Required(p,"artifact"));
            if(artifactNode.Element("payloadKind")?.Value!="theme-zip") throw new InvalidOperationException("ThemePayloadKind");
            artifactNode.Element("payloadKind").Value="managed-dll-zip";
            PackageVersion version;if(!PackageVersion.TryParse(manifest.Version.ToString(),out version)) throw new InvalidOperationException("InvalidVersion");
            var artifact=CatalogReader.ReadArtifact(artifactNode,version,true);
            if(artifact.SizeBytes>ThemePackage.MaximumPackageBytes) throw new InvalidOperationException("ThemePackageLimit");
            if(args[0]!="theme-payload" || id!=args[4] || manifest.Version.ToString()!=args[5]) continue;
            if(state!="active") throw new InvalidOperationException("ThemeInactive");
            using(var input=File.OpenRead(args[3]))
            {
                var package=ThemePackage.Read(input,CancellationToken.None);
                if(package.Length!=artifact.SizeBytes || package.Sha256!=artifact.Sha256 || package.ManifestSha256!=artifact.ManifestSha256 ||
                    !Json(CatalogReader.ReadJson(package.CopyFile("manifest.json")),true).SequenceEqual(Json(declared,true))) throw new InvalidOperationException("ThemePayloadMismatch");
                File.WriteAllText(args[6],System.Text.Json.JsonSerializer.Serialize(new {packageId=id,version=manifest.Version.ToString(),sha256=package.Sha256,manifestSha256=package.ManifestSha256,validation="static-data-only"}));verified=true;
            }
        }
        if(args[0]=="theme-payload" && !verified) throw new InvalidOperationException("ThemePackageNotFound");
        Console.WriteLine("Theme data catalog/payload verified without loading code.");return 0;
    }
}
