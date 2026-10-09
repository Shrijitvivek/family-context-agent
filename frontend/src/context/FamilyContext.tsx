import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  getFamilies,
  getFamilyMembers,
  type Family,
  type FamilyMember,
} from "../services/api/families";

interface FamilyContextValue {
  families: Family[];
  selectedFamilyId: string | null;
  setSelectedFamilyId: (familyId: string) => void;

  members: FamilyMember[];
  selectedMemberId: string | null;
  setSelectedMemberId: (memberId: string) => void;

  loading: boolean;
  error: string | null;
}

const FamilyContext = createContext<FamilyContextValue | undefined>(
  undefined
);

interface FamilyProviderProps {
  children: ReactNode;
}

export function FamilyProvider({ children }: FamilyProviderProps) {
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamilyId, setSelectedFamilyId] = useState<string | null>(
    null
  );

  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(
    null
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadFamilies = async () => {
      try {
        const data = await getFamilies();
        setFamilies(data);

        const demoFamilyId = localStorage.getItem("demo_family_id");

        if (
          demoFamilyId &&
          data.some((family) => family.id === demoFamilyId)
        ) {
          setSelectedFamilyId(demoFamilyId);
        } else if (data.length > 0) {
          setSelectedFamilyId(data[0].id);
        }
      } catch {
        setError("Unable to load families.");
      } finally {
        setLoading(false);
      }
    };

    loadFamilies();
  }, []);

  useEffect(() => {
    if (!selectedFamilyId) {
      setMembers([]);
      setSelectedMemberId(null);
      return;
    }

    const loadMembers = async () => {
      try {
        const data = await getFamilyMembers(selectedFamilyId);

        setMembers(data);

        const firstActiveMember = data.find((member) => member.is_active);

        setSelectedMemberId(firstActiveMember?.id ?? null);
      } catch {
        setMembers([]);
        setSelectedMemberId(null);
        setError("Unable to load family members.");
      }
    };

    loadMembers();
  }, [selectedFamilyId]);

  return (
    <FamilyContext.Provider
      value={{
        families,
        selectedFamilyId,
        setSelectedFamilyId,
        members,
        selectedMemberId,
        setSelectedMemberId,
        loading,
        error,
      }}
    >
      {children}
    </FamilyContext.Provider>
  );
}

export function useFamily() {
  const context = useContext(FamilyContext);

  if (!context) {
    throw new Error("useFamily must be used inside FamilyProvider");
  }

  return context;
}