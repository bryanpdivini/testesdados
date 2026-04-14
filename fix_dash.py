import codecs

try:
    with codecs.open('dashboard.html', 'r', encoding='utf-8') as f:
        text = f.read()
except UnicodeDecodeError:
    with codecs.open('dashboard.html', 'r', encoding='cp1252') as f:
        text = f.read()

target = '''        tooltip:{callbacks:{label:v=>v.label+': '+v.raw.toLocaleString('pt-BR')+
          ' ('+((v.raw/data.length)*100).toFixed(1)+'%)'}}}
      }
    }
  });'''
replacement = '''        tooltip:{callbacks:{label:v=>v.label+': '+v.raw.toLocaleString('pt-BR')+
          ' ('+((v.raw/data.length)*100).toFixed(1)+'%)'}}}
      }
  });'''

text = text.replace(target, replacement)

replacements = {
    'Eltrico': 'Elétrico', 'El\xef\xbf\xbd\xef\xbf\xbd\xef\xbf\xbdtrico': 'Elétrico',
    'Eltrico': 'Elétrico',
    'Hbrido': 'Híbrido', 'No Informado': 'Não Informado',
    'Econmico': 'Econômico', 'Baixa Relevncia': 'Baixa Relevância',
    'Disponvel': 'Disponível', 'Analtico': 'Analítico',
    'Mdio': 'Médio', 'Mdio': 'Médio',
    'Converso': 'Conversão', 'Anncios': 'Anúncios'
}

for k, v in replacements.items():
    text = text.replace(k, v)

# In case some cp1252 to utf8 failed
text = text.replace('', '')

with codecs.open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
