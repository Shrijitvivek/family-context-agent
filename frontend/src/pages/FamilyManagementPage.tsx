
import { useEffect, useState, type FormEvent } from "react";

import { useFamily } from "../context/FamilyContext";
import {
  addFamilyMember,
  getFamilyMembers,
  type FamilyMember,
} from "../services/api/families";
import { createFamily } from "../services/api/families";

export default function FamilyManagementPage() {
  const {
    families,
    selectedFamilyId,
    setSelectedFamilyId,
    addFamilyToContext,
  } = useFamily();

  const [familyName, setFamilyName] = useState("");

  const [memberName, setMemberName] = useState("");
  const [relationship, setRelationship] = useState("OTHER");
  const [displayRole, setDisplayRole] = useState("");

  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!selectedFamilyId) {
      setMembers([]);
      return;
    }

    let cancelled = false;

    async function loadMembers() {
      setLoading(true);
      setError("");

      try {
        const result = await getFamilyMembers(selectedFamilyId!);

        if (!cancelled) {
          setMembers(result);
        }
      } catch {
        if (!cancelled) {
          setError("Unable to load family members.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    void loadMembers();

    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId]);

  async function handleCreateFamily(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSuccess("");
    setSaving(true);

    try {
      const family = await createFamily({
        name: familyName.trim(),
      });

      addFamilyToContext(family);
      setFamilyName("");
      setSuccess(`Family "${family.name}" created successfully.`);
    } catch {
      setError("Unable to create family. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  async function handleAddMember(event: FormEvent) {
    event.preventDefault();

    if (!selectedFamilyId) {
      setError("Select a family before adding a member.");
      return;
    }

    setError("");
    setSuccess("");
    setSaving(true);

    try {
      const member = await addFamilyMember(selectedFamilyId, {
        name: memberName.trim(),
        relationship_type: relationship,
        display_role: displayRole.trim() || null,
      });

      setMembers((current) =>
        [...current, member].sort((a, b) =>
          a.name.localeCompare(b.name),
        ),
      );

      setMemberName("");
      setDisplayRole("");
      setRelationship("OTHER");
      setSuccess(`${member.name} added successfully.`);
    } catch {
      setError("Unable to add member. Please try again.");
    } finally {
      setSaving(false);
    }
  }

  const activeMembers = members.filter(
    (member) => member.is_active,
  );

  return (
    <main className="mx-auto max-w-4xl space-y-6 p-4 sm:p-6">
      <header>
        <h1 className="text-2xl font-bold text-slate-900">
          Family Management
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Create households and manage their members.
        </p>
      </header>

      {error && (
        <p role="alert" className="rounded-lg bg-red-50 p-3 text-sm text-red-700">
          {error}
        </p>
      )}

      {success && (
        <p role="status" className="rounded-lg bg-green-50 p-3 text-sm text-green-700">
          {success}
        </p>
      )}

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Create a family</h2>

        <form onSubmit={handleCreateFamily} className="mt-4 space-y-4">
          <div>
            <label htmlFor="family-name" className="mb-1 block text-sm font-medium">
              Family name
            </label>
            <input
              id="family-name"
              required
              maxLength={150}
              value={familyName}
              onChange={(event) => setFamilyName(event.target.value)}
              placeholder="e.g. Aamir Family"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <button
            type="submit"
            disabled={saving || !familyName.trim()}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {saving ? "Saving..." : "Create family"}
          </button>
        </form>
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold">Add family members</h2>

        <div className="mt-4">
          <label htmlFor="manage-family" className="mb-1 block text-sm font-medium">
            Select family
          </label>
          <select
            id="manage-family"
            value={selectedFamilyId ?? ""}
            onChange={(event) => setSelectedFamilyId(event.target.value)}
            className="w-full rounded-lg border border-slate-300 px-3 py-2"
          >
            <option value="" disabled>
              Select a family
            </option>
            {families.map((family) => (
              <option key={family.id} value={family.id}>
                {family.name}
              </option>
            ))}
          </select>
        </div>

        <form onSubmit={handleAddMember} className="mt-4 space-y-4">
          <div>
            <label htmlFor="member-name" className="mb-1 block text-sm font-medium">
              Member name
            </label>
            <input
              id="member-name"
              required
              maxLength={150}
              value={memberName}
              onChange={(event) => setMemberName(event.target.value)}
              placeholder="Enter member name"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <div>
            <label htmlFor="relationship" className="mb-1 block text-sm font-medium">
              Relationship
            </label>
            <select
              id="relationship"
              value={relationship}
              onChange={(event) => setRelationship(event.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            >
              <option value="SELF">Self</option>
              <option value="SPOUSE">Spouse</option>
              <option value="PARENT">Parent</option>
              <option value="CHILD">Child</option>
              <option value="SIBLING">Sibling</option>
              <option value="OTHER">Other</option>
            </select>
          </div>

          <div>
            <label htmlFor="display-role" className="mb-1 block text-sm font-medium">
              Display role (optional)
            </label>
            <input
              id="display-role"
              maxLength={100}
              value={displayRole}
              onChange={(event) => setDisplayRole(event.target.value)}
              placeholder="e.g. Family administrator"
              className="w-full rounded-lg border border-slate-300 px-3 py-2"
            />
          </div>

          <button
            type="submit"
            disabled={saving || !selectedFamilyId || !memberName.trim()}
            className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {saving ? "Saving..." : "Add member"}
          </button>
        </form>

        <div className="mt-6 border-t border-slate-200 pt-4">
          <h3 className="font-semibold">
            Members ({activeMembers.length})
          </h3>

          {loading ? (
            <p className="mt-3 text-sm text-slate-500">Loading members...</p>
          ) : activeMembers.length === 0 ? (
            <p className="mt-3 text-sm text-slate-500">
              No active members in this family yet.
            </p>
          ) : (
            <ul className="mt-3 divide-y divide-slate-100">
              {activeMembers.map((member) => (
                <li
                  key={member.id}
                  className="flex items-center justify-between gap-3 py-3"
                >
                  <div>
                    <p className="font-medium text-slate-900">{member.name}</p>
                    <p className="text-sm text-slate-500">
                      {member.relationship_type.replaceAll("_", " ")}
                      {member.display_role ? ` · ${member.display_role}` : ""}
                    </p>
                  </div>
                  <span className="rounded-full bg-green-50 px-2 py-1 text-xs text-green-700">
                    Active
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </main>
  );
}
