"""Safe deterministic SEO drafts. Does not claim to know real trends/analytics."""
import re

STYLES = {
 'mind': {'hook':'Ce ai face dacă ai descoperi că {topic}?','cta':'Spune-ne ce semnal de alarmă ai observat.','tags':['#FruitMind','#Psihologie','#Povesti3D','#ComportamentUman'], 'caution':'Conținut de divertisment și educație, nu diagnostic.'},
 'wealth': {'hook':'O singură decizie financiară poate schimba povestea: {topic}.','cta':'Ce lecție financiară ai învățat din episod?','tags':['#FruitWealth','#EducatieFinanciara','#Bani','#Povesti3D'], 'caution':'Educație generală, nu recomandare de investiții.'},
 'beats': {'hook':'Un fruct. O voce. O melodie originală despre {topic}.','cta':'Ce fruct ai vrea să cânte în episodul următor?','tags':['#FruitBeats','#MuzicaOriginala','#ArtistVirtual','#3DAnimation'], 'caution':'Folosește numai muzică originală sau cu drepturi comerciale verificate.'},
 'lab': {'hook':'AFINA investighează: ce se întâmplă când {topic}?','cta':'Ce experiment vrei să explicăm în episodul următor?','tags':['#FruitLab','#Stiinta','#Experimente','#Curiozitati'], 'caution':'Verifică afirmațiile științifice și marchează simulările.'},
 'heart': {'hook':'O poveste despre dragoste începe cu o întrebare: {topic}.','cta':'Tu ce ai face în locul personajelor?','tags':['#FruitHeart','#Relatii','#PovestiDeDragoste','#Animatie3D'], 'caution':'Poveste ficțională; evită generalizările despre relații.'},
}

def clean(value: str, limit=180):
    value = re.sub(r'[\r\n\t]+',' ',value or '')
    return re.sub(r'\s+',' ',value).strip()[:limit]

def draft(channel_id:str, topic:str, content_type:str):
    if channel_id not in STYLES:
        raise ValueError('Canal invalid')
    if content_type not in {'main90','short15','image','longform'}:
        raise ValueError('Tip invalid')
    topic = clean(topic,140)
    if len(topic)<3: raise ValueError('Subiectul este prea scurt')
    s=STYLES[channel_id]
    hook=s['hook'].format(topic=topic)
    name={'mind':'FRUIT MIND','wealth':'FRUIT WEALTH','beats':'FRUIT BEATS','lab':'FRUIT LAB','heart':'FRUIT HEART'}[channel_id]
    title = clean(f'{topic[0].upper() + topic[1:]} | {name}',100)
    desc=f'{hook}\n\nÎn acest episod original {name} explorăm {topic}. Descoperă povestea și urmărește următorul episod.\n\n{s["cta"]}'
    tags=' '.join(s['tags'])
    prefix='🎬 ' if content_type != 'image' else '🖼️ '
    return {
     'status':'DRAFT_TEMPLATE','title':title,'hook':hook,'cta':s['cta'],'hashtags':s['tags'],
     'instagram':{'caption':prefix+desc+'\n\n'+tags,'format':'Reel' if content_type != 'image' else 'Imagine / carusel'},
     'tiktok':{'caption':clean(hook+' '+s['cta'],140)+' '+tags,'format':'Video vertical / fotografie'},
     'youtube':{'title':title,'description':desc+'\n\n'+tags,'format':'Shorts vertical' if content_type in {'main90','short15'} else 'Video lung 16:9' if content_type=='longform' else 'Community / imagine'},
     'storyboard':['0–3s: hook vizual și replica principală','Introducere: un personaj recurent și o situație clară','Dezvoltare: două-trei cadre cinematice, tranziții și dialog','Final: concluzie + CTA original'],
     'character_prompt':f'Original premium cinematic 3D anthropomorphic fruit character for {name}, consistent with approved character bible, expressive eyes, detailed face, textured surface, theatrical lighting, cinematic wardrobe; theme: {topic}.',
     'video_prompt':f'9:16 cinematic 3D sequence, original anthropomorphic fruit actor, expressive gestures and naturally synchronized mouth, continuous character identity; story topic: {topic}.',
     'review_warning':s['caution']+' Descrierile sunt propuneri, nu SEO validat prin date live.'
    }
