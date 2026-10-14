"""Shared catalog facts from a schema1 manifest or schema2 runtime envelope; never flatten payloads."""
import json

def variants(manifest):
    if type(manifest) is not dict:raise ValueError('ManifestObject')
    if type(manifest.get('schemaVersion')) is not int:raise ValueError('ManifestSchema')
    if manifest.get('schemaVersion')==1:return [manifest]
    if set(manifest)!= {'schemaVersion','variants'} or manifest.get('schemaVersion')!=2 or type(manifest['variants']) is not list or not 1<=len(manifest['variants'])<=2:raise ValueError('ManifestVariants')
    result=manifest['variants'];games=set();first=None
    for value in result:
        if type(value) is not dict or type(value.get('schemaVersion')) is not int or value.get('schemaVersion')!=1:raise ValueError('ManifestVariant')
        version=value['compatibility']['rimWorldVersions']
        if len(version)!=1 or version[0] not in ['1.6','1.7'] or version[0] in games or value['targetFramework']!={'1.6':'net472','1.7':'net10.0'}[version[0]]:raise ValueError('ManifestProfile')
        games.add(version[0]);identity={key:value[key] for key in ['packageId','name','version','modules','dependencies','externalMods']}
        if first is not None and identity!=first:raise ValueError('ManifestVariantIdentity')
        first=identity
    return result

def primary(manifest):return variants(manifest)[0]
def product_version(manifest):return primary(manifest)['version']
def resource_prefix(manifest):return '' if manifest.get('schemaVersion')==1 else primary(manifest)['compatibility']['rimWorldVersions'][0]+'/'
def scope(manifest):
    return sorted(json.dumps({'targetFramework':v['targetFramework'],'compatibility':v['compatibility'],'externalMods':v['externalMods']},sort_keys=True,separators=(',',':')) for v in variants(manifest))
