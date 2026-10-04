import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import {
  getFamilies,
  type Family,
} from "../services/api/families";

interface FamilyContextValue {
  families: Family[];
  selectedFamilyId: string | null;
  setSelectedFamilyId: (familyId: string) => void;
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
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadFamilies = async () => {
      try {
        const data = await getFamilies();
        setFamilies(data);

        if (data.length > 0) {
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

  return (
    <FamilyContext.Provider
      value={{
        families,
        selectedFamilyId,
        setSelectedFamilyId,
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
