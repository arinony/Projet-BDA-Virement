-- ==========================================
-- LOGIQUE MÉTIER : Procédure de virement atomique
-- ==========================================

CREATE OR REPLACE PROCEDURE p_virement(src INT, dst INT, val DECIMAL)
AS $$
BEGIN
    -- 1. Débiter le compte source
    UPDATE comptes SET solde = solde - val WHERE id_compte = src;
    
    -- 2. Créditer le compte destination
    UPDATE comptes SET solde = solde + val WHERE id_compte = dst;
    
    -- 3. Enregistrer la transaction dans l'historique
    -- Note : Cette insertion va déclencher le trigger 'trg_virement_securite'
    INSERT INTO transactions (id_source, id_dest, montant) 
    VALUES (src, dst, val);
    
    -- Si tout est OK, on valide les changements
    COMMIT;
END;
$$ LANGUAGE plpgsql;