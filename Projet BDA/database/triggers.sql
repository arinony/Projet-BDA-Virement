-- ==========================================
-- SÉCURITÉ : Vérification du solde avant virement
-- ==========================================

CREATE OR REPLACE FUNCTION fn_verifier_solde()
RETURNS TRIGGER AS $$
DECLARE
    solde_dispo DECIMAL;
BEGIN
    -- Récupération du solde du compte source (NEW.id_source)
    SELECT solde INTO solde_dispo FROM comptes WHERE id_compte = NEW.id_source;

    -- Si le solde est insuffisant, on lève une exception
    -- Cela annule automatiquement la transaction
    IF solde_dispo < NEW.montant THEN
        RAISE EXCEPTION 'ERREUR BDA : Solde insuffisant sur le compte source (%) !', NEW.id_source;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger qui se déclenche AVANT chaque insertion dans la table transactions
CREATE TRIGGER trg_virement_securite
BEFORE INSERT ON transactions
FOR EACH ROW EXECUTE FUNCTION fn_verifier_solde();