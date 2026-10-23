
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
  setSelectedMemberId: (memberId: string | null) => void;

  loading: boolean;
  error: string | null;
}

const FamilyContext = createContext<FamilyContextValue | undefined>(
  undefined,
);

interface FamilyProviderProps {
  children: ReactNode;
}

const getMemberStorageKey = (familyId: string) =>
  `selected_member:${familyId}`;

export function FamilyProvider({ children }: FamilyProviderProps) {
  const [families, setFamilies] = useState<Family[]>([]);
  const [selectedFamilyId, setSelectedFamilyIdState] =
    useState<string | null>(() => {
      return localStorage.getItem("selected_family_id");
  });

  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [selectedMemberId, setSelectedMemberId] = useState<string | null>(
    null,
  );

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const handleSetSelectedFamilyId = (familyId: string) => {
    setSelectedFamilyIdState(familyId);
    localStorage.setItem("selected_family_id", familyId);
  };

  useEffect(() => {
    const loadFamilies = async () => {
      try {
        
        const data = await getFamilies();
        setFamilies(data);

        const savedFamilyId = localStorage.getItem("selected_family_id");
        const savedFamilyExists = data.some(
          (family) => family.id === savedFamilyId
        );

        const demoFamilyId = localStorage.getItem("demo_family_id");
        const demoFamilyExists = data.some(
          (family) => family.id === demoFamilyId
        );

        const familyToSelect =
          savedFamilyId && savedFamilyExists
            ? savedFamilyId
            : demoFamilyId && demoFamilyExists
              ? demoFamilyId
              : data[0]?.id ?? null;

        if (familyToSelect) {
          setSelectedFamilyIdState(familyToSelect);
          localStorage.setItem("selected_family_id", familyToSelect);
        }

      } catch {
        setError("Unable to load families.");
      } finally {
        setLoading(false);
      }
    };

    void loadFamilies();
  }, []);

  useEffect(() => {
    if (!selectedFamilyId) {
      setMembers([]);
      setSelectedMemberId(null);
      return;
    }

    let cancelled = false;

    const loadMembers = async () => {
      try {
        const data = await getFamilyMembers(selectedFamilyId);

        if (cancelled) return;

        setMembers(data);

        const activeMembers = data.filter((member) => member.is_active);
        const savedMemberId = localStorage.getItem(
          getMemberStorageKey(selectedFamilyId),
        );

        const savedMemberIsActive = activeMembers.some(
          (member) => member.id === savedMemberId,
        );

        setSelectedMemberId(
          savedMemberIsActive ? savedMemberId : null,
        );
      } catch {
        if (cancelled) return;

        setMembers([]);
        setSelectedMemberId(null);
        setError("Unable to load family members.");
      }
    };

    void loadMembers();

    return () => {
      cancelled = true;
    };
  }, [selectedFamilyId]);

  const handleSetSelectedMemberId = (memberId: string | null) => {
    setSelectedMemberId(memberId);

    if (!selectedFamilyId) return;

    if (memberId === null) {
      localStorage.removeItem(getMemberStorageKey(selectedFamilyId));
    } else {
      localStorage.setItem(
        getMemberStorageKey(selectedFamilyId),
        memberId,
      );
    }
  };

  return (
    <FamilyContext.Provider
      value={{
        families,
        selectedFamilyId,
        setSelectedFamilyId: handleSetSelectedFamilyId,
        members,
        selectedMemberId,
        setSelectedMemberId: handleSetSelectedMemberId,
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
