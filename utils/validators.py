import re

class CNPJValidator:
    @staticmethod
    def validate(cnpj: str) -> bool:
        """
        Valida se um CNPJ é válido baseando-se nos dígitos verificadores (Algoritmo Módulo 11).
        Recebe: string (com ou sem pontuação).
        Retorna: True/False.
        """
        if not cnpj:
            return False

        # 1. Limpeza: Remove tudo que não for dígito
        cnpj = re.sub(r'\D', '', str(cnpj))

        # 2. Verificações de Tamanho e Sequências Inválidas
        if len(cnpj) != 14 or len(set(cnpj)) == 1:
            return False

        # 3. Cálculo do Primeiro Dígito Verificador
        # Pesos: [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos_1[i] for i in range(12))
        resto = soma % 11
        digito_1 = 0 if resto < 2 else 11 - resto

        if int(cnpj[12]) != digito_1:
            return False

        # 4. Cálculo do Segundo Dígito Verificador
        # Pesos: [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        pesos_2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos_2[i] for i in range(13))
        resto = soma % 11
        digito_2 = 0 if resto < 2 else 11 - resto

        if int(cnpj[13]) != digito_2:
            return False

        return True

    @staticmethod
    def format(cnpj: str) -> str:
        """Formata CNPJ para XX.XXX.XXX/XXXX-XX"""
        cnpj = re.sub(r'\D', '', str(cnpj))
        if len(cnpj) != 14:
            return cnpj # Retorna sujo se não tiver tamanho
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"