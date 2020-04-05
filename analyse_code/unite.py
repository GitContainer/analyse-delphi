import re
from pathlib import Path
import codecs

from .log import *
from .gestion_multiligne import *
from .data import *
from .uses import *
from .regex import *
from .type import *

class unite():
    def __init__(self, nom_fichier):
        self.data = ''
        self.gestion_ml = None
        self.nom_fichier = Path(nom_fichier)
        self.nom = ''
        with codecs.open(str(nom_fichier), 'r', encoding='utf-8-sig') as f:
            lignes = f.readlines()
            self.gestion_ml = gestion_multiligne.gestion_multiligne(lignes)
            self.data = cData(self.gestion_ml)

        logger.info('Analyse du fichier <%s>', str(self.nom_fichier))
        self.pos_unite = self._find_unit()
        self.nom = self.pos_unite[3][0]
        self.liste_classe = []
        self.liste_section_interface = []
        self.liste_fonction = []
        self.type_interface_pos = []
        self.liste_type_interface = []
        self.symbols = cTableSymbol()
        self.uses_inter_pos = self.uses_interface = None
        self.uses_impl_pos = self.uses_implementation = None
        self.liste_unite = []
        self.interface_pos = self._find_interface()
        if self.interface_pos is None:
            logger.error('impossible de trouver la section interface')
        self.implementation_pos = self._find_implementation()
        if self.implementation_pos is None:
            logger.error('impossible de trouver la section implementation')
        self.end_final_pos = self._find_endfinal()
        if self.end_final_pos is None:
            logger.error('impossible de trouver le end final')
        if (self.interface_pos is not None) and (self.implementation_pos is not None):
            self.uses_inter_pos = self._find_uses(self.interface_pos[1], self.implementation_pos[0])
            self.uses_impl_pos = self._find_uses(self.implementation_pos[1], self.end_final_pos[0])
            if self.uses_inter_pos is not None:
                self.uses_interface = cUses(self.uses_inter_pos[3][0])
            if self.uses_impl_pos is not None:
                self.uses_implementation = cUses(self.uses_impl_pos[3][0])

    def analyse_type_interface(self):
        self.type_interface_pos, self.liste_type_interface = self._analyse_type(self.interface_pos[1], self.implementation_pos[0])
        # on cherche les functions / procedure entre les sections type
        debut = self.interface_pos[1]
        logger.debug('analyse_type_interface : liste pos %s', str(self.type_interface_pos))
        for pos in self.type_interface_pos:
            fin = pos[0]
            pos_function = self._find_function(debut, fin)
            while pos_function is not None:
                logger.debug('analyse_type_interface : fonction trouve %s', str(pos_function))
                pos_function = self._find_function(pos_function[1], fin)
            debut = pos[1]
        fin = self.implementation_pos[0]
        pos_function = self._find_function(debut, fin)
        while pos_function is not None:
            self.symbols.ajouter(pos_function[3][0], cType('function', '', None), self.data.genere_fils(pos_function[0], pos_function[1]))
            logger.debug('analyse_type_interface : fonction trouve %s', str(pos_function))
            pos_function = self._find_function(pos_function[1], fin)

    def _analyse_type(self, start_point, end_point):
        logger.info('debut analyse type')
        type_pos = []
        liste_type = []
        pos = self._find_type(start_point, end_point)
        while pos is not None:
            logger.info('section type trouve %s', str(pos))
            liste_type.append(self._analyse_section_type(pos[1], end_point))
            type_pos.append((pos[0], liste_type[-1].data.end_point))
            pos = self._find_type(liste_type[-1].data.end_point, end_point)
        return (type_pos, liste_type)


    def __str__(self):
        chaine = 'UNITE <%s> <%s> utilise par <%d>\n' % (self.nom, str(self.nom_fichier), len(self.liste_unite))
        chaine += '\tINTERFACE Ligne : %d\n' % self.gestion_ml.num_ligne(self.interface_pos[0])
        if self.uses_interface is not None:
            chaine += '\t\t' + str(self.uses_interface) + '\n'
        for t in self.liste_type_interface:
            chaine += '\t\t' + str(t) + '\n'
        chaine += '\tIMPLEMENTATION cLigne : %d\n' % self.gestion_ml.num_ligne(self.implementation_pos[0])
        if self.uses_implementation is not None:
            chaine += '\t\t' + str(self.uses_implementation) + '\n'
        chaine += '\t%s\n' % str(self.symbols)

        for iclass in self.liste_classe:
            chaine += str(iclass)
        for ifct in self.liste_fonction:
            chaine += str(ifct)
        return chaine

    def _find_unit(self):
        return self.data._find_regex(C_RE_UNIT, 0, -1)
    def _find_interface(self):
        return self.data._find_regex(C_RE_INTERFACE, 0, -1)
    def _find_implementation(self):
        return self.data._find_regex(C_RE_IMPLEMENTATION, 0, -1)
    def _find_endfinal(self):
        return self.data._find_regex(C_RE_END_FINAL, 0, -1)

    def _find_function(self, start_point, end_point, impl=''):
        match_obj = None
        verb = 'function'
        liste_group = [ ]
        if impl == '':
            match_obj = self.data._find_regex(C_RE_FUNCTION_DECL_S, start_point, end_point)
            if match_obj is None:
                match_obj = self.data._find_regex(C_RE_FUNCTION_DECL, start_point, end_point)
            match_obj_proc = self.data._find_regex(C_RE_PROCEDURE_DECL_S, start_point, end_point)
            if match_obj_proc is None:
                match_obj_proc = self.data._find_regex(C_RE_PROCEDURE_DECL, start_point, end_point)
            # la procedure est avant la function on garde la procedure
            if ((match_obj is not None) and (match_obj_proc is not None) and (match_obj_proc[0] < match_obj[0])) or\
               ((match_obj is None) and (match_obj_proc is not None)):
                verb = 'procedure'
                match_obj = match_obj_proc
        else:
            match_obj = self.data._find_regex(C_RE_FUNCTION_IMPL_S % impl, start_point, end_point)
            if match_obj is None:            
                match_obj = self.data._find_regex(C_RE_FUNCTION_IMPL % impl, start_point, end_point)
            match_obj_proc = self.data._find_regex(C_RE_PROCEDURE_IMPL_S % impl, start_point, end_point)
            if match_obj_proc is None:
                match_obj_proc = self.data._find_regex(C_RE_PROCEDURE_IMPL % impl, start_point, end_point)
            # la procedure est avant la function on garde la procedure
            if match_obj_proc[0] < match_obj[0]:
                match_obj = match_obj_proc
        if match_obj is not None:
            logger.debug('resultat detection function/procedure : %s', str(match_obj[3]))
            group_match = match_obj[3]
            if len(match_obj[3]) == 4:
                match_obj_param = re.finditer(C_RE_PARAM, group_match[1])
                for match_iter in match_obj_param:
                    liste_param = match_iter.groups()[1]
                    if (liste_param == '') or (liste_param is None):
                        logger.error('nom de parametre non trouve dans fonction %s', group_match[0])
                    for param in liste_param.split(','):
                        liste_group.append((match_iter.groups()[0], param.strip(), match_iter.groups()[2]))
                group_match = (group_match[0], liste_group, group_match[2])
            else:
                group_match = (group_match[0], [], group_match[1], group_match[2])
            return (match_obj[0], match_obj[1], match_obj[2], group_match, verb)
        return None
    def _find_procedure(self, start_point, end_point, impl=''):
        match_obj = None
        if impl == '':
            match_obj = self.data._find_regex(C_RE_PROCEDURE_DECL_S, start_point, end_point)
            if match_obj is None:
                match_obj = self.data._find_regex(C_RE_PROCEDURE_DECL, start_point, end_point)
        else:
            match_obj = self.data._find_regex(C_RE_PROCEDURE_IMPL_S % impl, start_point, end_point)
            if match_obj is None:
                match_obj = self.data._find_regex(C_RE_PROCEDURE_IMPL % impl, start_point, end_point)
        if match_obj is not None:
            group_match = match_obj[3]
            if len(match_obj[3]) == 3:
                match_obj_param = re.finditer(C_RE_PARAM, group_match[1])
                liste_group = [ ]
                for match_iter in match_obj_param:
                    liste_param = match_iter.groups()[1]
                    if (liste_param == '') or (liste_param is None):
                        logger.error('nom de parametre non trouve dans procedure %s', group_match[0])
                    for param in liste_param.split(','):
                        liste_group.append((match_iter.groups()[0], param.strip(), match_iter.groups()[2]))
                group_match = (group_match[0], liste_group)
            else:
                group_match = (group_match[0], [])
            return (match_obj[0], match_obj[1], match_obj[2], group_match)
        return None

    def _find_uses(self, start_point, end_point):
        return self.data._find_regex(C_RE_USES, start_point, end_point)

    def _find_type(self, start_point, end_point):
        return self.data._find_regex(C_RE_TYPES, start_point, end_point)

    def _find_class(self, start_point, end_point):
        match_pos = self.data._find_regex(C_RE_CLASS_DEB, start_point, end_point)
        end_pos = None
        if match_pos is not None:
            logger.debug('find_class : debut de class trouve type %s', match_pos[3][2])
            current_pos = match_pos[1]
            # on cherche le premier end
            end_pos = self.data._find_regex(C_RE_END, current_pos, end_point)
            # on cherche une section type
            pos_type = self._find_type(current_pos, end_point)
            # si type detecte et avant premier end
            if (pos_type is not None) and (end_pos is not None) and (pos_type[1] < end_pos[1]):
                current_pos = pos_type[1]
                logger.debug('find_class : section type trouve : %d %d', current_pos,end_pos[1])
                while True:
                    match_pos_class = self.data._find_regex(C_RE_CLASS_DEB, current_pos, end_pos[1])
                    # on a trouve une classe avant le end
                    if (match_pos_class is not None):
                        logger.debug('classe fille trouve ligne : %d', self.num_ligne(start_point + current_pos + match_pos_class[0]))
                        # on cherche le prochain end
                        end_pos = self.data._find_regex(C_RE_END, end_pos[1], end_point)
                        current_pos = end_pos[1]
                        logger.debug('end trouve ligne : %s', str(end_pos))
                    else:
                        break
            if end_pos is not None:
                return (match_pos[0], end_pos[1], self.gestion_ml.num_ligne(match_pos[0]), self.gestion_ml.num_ligne(end_pos[1]), match_pos[3])
        return None
    def _find_record(self, start_point, end_point):
        return self.data._find_regex(C_RE_RECORD, start_point, end_point)

    def _find_type_proc_func(self, start_point, end_point):
        return self.data._find_regex(C_RE_TYPE_PROC_FUNC, start_point, end_point)

    def _find_type_decl(self, start_point, end_point):
        return self.data._find_regex(C_RE_DECL_TYPE, start_point, end_point)

    def _analyse_section_type(self, start_point, end_point):
        resultat = { 'class': [], 'record': [], 'type': [], 'setof': [], 'type_procedure': [], 'finsection': end_point}
        resultat = cEnsembleType(self.data.genere_fils(start_point, end_point))
        current_pos = start_point
        logger.debug('analyse type : %s', self.data.data[current_pos:current_pos+30])
        # d'abord on saute les premiers espace
        espace_pos = self.data._find_regex(r'\s*', current_pos, -1)
        if espace_pos is not None:
            logger.debug('espace trouve : %s %d', str(espace_pos), espace_pos[1] + 1)
            current_pos = espace_pos[1]
        while current_pos < end_point:
            logger.debug('analyse type : %s', self.data.data[current_pos:current_pos+30])
            # on recherche une classe
            class_pos = self._find_class(current_pos, end_point)
            if (class_pos is not None) and (class_pos[0] == current_pos):
                logger.info('classe trouve : %s', str(class_pos))
                current_pos = class_pos[1] + 1
                if class_pos[4][1] == 'CLASS':
                    resultat.ajouter(cClasse(class_pos[4][0], class_pos[4][2], self.data.genere_fils(class_pos[0], class_pos[1])))
                else:
                    resultat.ajouter(cType(class_pos[4][0], '', self.data.genere_fils(class_pos[0], class_pos[1]), p_type=class_pos[4][1]))
                # resultat['class'].append(class_pos) 
            else:
                typefunc_pos = self._find_type_proc_func(current_pos, end_point)
                if (typefunc_pos is not None) and (typefunc_pos[0] == current_pos):
                    logger.info('type procedure trouve')
                    current_pos = typefunc_pos[1] + 1
                    resultat.ajouter(cType(typefunc_pos[3][0], '', self.data.genere_fils(typefunc_pos[0], typefunc_pos[1])))
                    # resultat['type_procedure'].append(typefunc_pos) 
                else:
                    typedecl_pos = self._find_type_decl(current_pos, end_point)
                    if (typedecl_pos is not None) and (typedecl_pos[0] == current_pos):
                        logger.info('type declaration trouve')
                        current_pos = typedecl_pos[1] + 1
                        resultat.ajouter(cType(typedecl_pos[3][0], '', self.data.genere_fils(typedecl_pos[0], typedecl_pos[1])))
                        # resultat['type'].append(typedecl_pos) 
                    else:
                        logger.error('type non trouve')
                        # resultat['finsection'] = current_pos
                        resultat.data.end_point = current_pos
                        logger.info('fin analyse type ; %s', str(resultat))
                        return resultat
            espace_pos = self.data._find_regex(r'\s*', current_pos, -1)
            if espace_pos is not None:
                # logger.debug('avant saut espace : %s', self.data[current_pos:current_pos+30])
                current_pos = espace_pos[1]
        # resultat['finsection'] = current_pos
        resultat.data.end_point = current_pos
        logger.info('fin analyse type ; %s', str(resultat))
        return resultat
    def num_ligne(self, position):
        return self.gestion_ml.num_ligne(position)