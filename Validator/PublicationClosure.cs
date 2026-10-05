using System;
using System.Collections.Generic;
using System.Linq;
using Phinix.PluginStore;
using Utils.Framework.ManagedExtensions;

// Repository closure only. Runtime host/game/installed-state checks still run in the client.
internal static class PublicationClosure
{
    internal static void Validate(ManagedStoreCatalogSnapshot catalog)
    {
        foreach (var root in catalog.Packages.Where(p => !p.IsWorkshop && p.State == "active"))
        {
            int steps = 0;
            if (!Search(catalog, root, new Dictionary<string, ManagedStoreRecord>(), ref steps))
                throw new InvalidOperationException("PublicationDependencyClosure");
        }
    }

    private static bool Search(ManagedStoreCatalogSnapshot catalog, ManagedStoreRecord root,
        Dictionary<string, ManagedStoreRecord> selected, ref int steps)
    {
        if (++steps > 4096 || selected.Count > 32) throw new InvalidOperationException("PublicationResolutionLimit");
        var required = new Dictionary<string, List<ManagedExtensionVersionRange>>();
        Add(required, root.Id, ManagedExtensionVersionRange.Parse(root.Manifest.Version.ToString()));
        foreach (var package in selected.Values)
            foreach (var dependency in package.Manifest.Dependencies)
                if (!dependency.Optional || catalog.Packages.Any(p => !p.IsWorkshop && p.State == "active" && p.Id == dependency.PackageId))
                    Add(required, dependency.PackageId, dependency.VersionRange);
        if (selected.Any(p => required.ContainsKey(p.Key) && required[p.Key].Any(r => !r.Contains(p.Value.Manifest.Version)))) return false;
        string next = required.Keys.Where(k => !selected.ContainsKey(k)).OrderBy(k => k, StringComparer.Ordinal).FirstOrDefault();
        if (next == null) return IdentitiesAndCycles(selected);
        foreach (var candidate in catalog.Packages.Where(p => !p.IsWorkshop && p.State == "active" && p.Id == next &&
            required[next].All(r => r.Contains(p.Manifest.Version))).OrderByDescending(p => p.Manifest.Version))
        {
            selected.Add(next, candidate);
            if (Search(catalog, root, selected, ref steps)) return true;
            selected.Remove(next);
        }
        return false;
    }

    private static void Add(Dictionary<string, List<ManagedExtensionVersionRange>> required, string id, ManagedExtensionVersionRange range)
    {
        List<ManagedExtensionVersionRange> values;
        if (!required.TryGetValue(id, out values)) required[id] = values = new List<ManagedExtensionVersionRange>();
        values.Add(range);
    }

    private static bool IdentitiesAndCycles(Dictionary<string, ManagedStoreRecord> selected)
    {
        var assemblies = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        var modules = new Dictionary<string, string[]>(StringComparer.OrdinalIgnoreCase);
        foreach (var package in selected.Values)
        {
            foreach (var assembly in package.Manifest.Assemblies) if (!assemblies.Add(assembly.Name)) return false;
            foreach (var module in package.Manifest.Modules)
            {
                if (modules.ContainsKey(module.Id)) return false;
                modules.Add(module.Id, module.DependsOn.ToArray());
            }
        }
        // Host-provided module dependencies need an explicitly reviewed allowlist in a later batch.
        if (modules.Values.Any(deps => deps.Any(d => !modules.ContainsKey(d)))) return false;
        foreach (string id in selected.Keys)
            if (!Visit(id, new HashSet<string>(), new HashSet<string>(), key => selected[key].Manifest.Dependencies
                .Where(d => selected.ContainsKey(d.PackageId)).Select(d => d.PackageId))) return false;
        foreach (string id in modules.Keys)
            if (!Visit(id, new HashSet<string>(), new HashSet<string>(), key => modules[key])) return false;
        return true;
    }

    private static bool Visit(string id, HashSet<string> seen, HashSet<string> stack, Func<string, IEnumerable<string>> children)
    {
        if (stack.Contains(id)) return false;
        if (!seen.Add(id)) return true;
        stack.Add(id);
        foreach (string child in children(id)) if (!Visit(child, seen, stack, children)) return false;
        stack.Remove(id);
        return true;
    }
}
