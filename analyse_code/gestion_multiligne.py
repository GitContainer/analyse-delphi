import re


class gestion_multiligne:
    def __init__(self, lignes, mode_modification=False):
        self.index = []
        self.index_reel = []
        self.lignes = []
        self.data = ''
        index_courant = 0
        index_courant_reel = 0
        # en mode modificatio on garde les lignes pour pouvoir les modifier.
        if mode_modification:
            self.lignes = lignes
        mode_saut = False
        for ligne in lignes:
            ligne_mod = re.sub(r'\(\*.*\*\)', ' ', ligne)
            ligne_mod = re.sub(r'\{.*?\}', ' ', ligne_mod)
            ligne_mod = ligne_mod.replace('{$REGION}', ' ')
            ligne_mod = ligne_mod.replace('{$ENDREGION}', ' ')
            pos_commentaire = ligne_mod.find('//')
            ligne_mod = ligne_mod[0:pos_commentaire] + ' '
            m_re = re.search(r'\*\)(?!\')', ligne_mod)
            if m_re is not None:
                mode_saut = False
                ligne_mod = ligne_mod[m_re.end(0):]
            if mode_saut:
                continue
            m_re = re.search(r'(?<!\')\(\*', ligne_mod)
            if m_re is not None:
                mode_saut = True
                ligne_mod = ligne_mod[0:m_re.start(0)]
            self.data += ligne_mod
            self.index.append(index_courant)
            self.index_reel.append(index_courant_reel)
            index_courant += len(ligne_mod)
            index_courant_reel += len(ligne)

    def num_ligne(self, indice):
        for pos in self.index:
            if pos > indice:
                return self.index.index(pos)
        if indice >= self.index[-1]:
            return len(self.index)
        raise Exception('numero de ligne non trouve')

    def pos_num_ligne(self, num_ligne):
        return self.index_reel[num_ligne - 1]
