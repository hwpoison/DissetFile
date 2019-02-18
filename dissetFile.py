/* minimalBot rev3 - code by srbill1990 */

lobuloTemporal = {
	'conteoError' : 0,
	'conteoRepeticion' : 0,
	'ultimoMensaje':[]
}

gadgetConversacion = document.getElementById("mbotConversacion")

gadgetConversacion.innerHTML+="<div id='caja-conteiner'>"+
							  "<input id='entradaDeUsuario' type='text' spellcheck='true' placeholder='Escriba algo..'>"+
							  "<div id='messageBox'></div>"+
							  "</div>"+
							  "<div id='notificacionEscritura'></div>"

var actualMessageAmount = 0
var maxMessageBox = 5
var responseTime = aMilisegundos(1.5)
var mutedTime = aMilisegundos(30)
var userInputBox = document.getElementById('entradaDeUsuario')
var messageBox = document.getElementById('messageBox')
var typingNotification = document.getElementById('notificacionEscritura')

var DEBUG = true
var DB_MBOT = minDb	  	

//Deteccion de la tecla enter
userInputBox.addEventListener("keyup", function(event) {
  event.preventDefault();
  if (event.keyCode === 13) {
	reply()
	userInputBox.value = ""
  }
});


//retorna milesegundos de una cantidad especifica de segundos
function aMilisegundos(seconds){
	return seconds*1000
}

function getKeys(dict){
	return Object.keys(dict)
}

function printf(mensaje){
	console.log(mensaje)
}

function randomItem(array){
	/* 
		Return random item in array 
	*/
	return array[Math.floor(Math.random() * (0 - array.length)) + array.length]
}
	
//Mensaje aleatorio de lista
function randomAnswer(answer_desc){
	array = ''
	if(answer_desc != 'aleatorio'){
		array = DB_MBOT[answer_desc]
		//si detecta un valor de referencia
		if(array[0][0] == '*' && array[0].slice(1) in DB_MBOT)
			array = DB_MBOT[array[0].slice(1)]
	}else{
		db =  getKeys(DB_MBOT)
		//retorna una pregunta aleatoria
		while(true){
			array = randomItem(db)
			if(array[0] == 'p'){
				array = DB_MBOT[array]
				break
			}
		}
	}
	return randomItem(array)
}


//Filtra los caracteres especiales y los separa para poder manipularlos.
//. revisar separacion de caracteres especiales
function filterString(string){
		special_characters = ['?', '!', '.', ',']
		special_characters = []
		if(string[0] != "+")//conservar mayusculas originales
			 process_string = string.toLowerCase()
		else
			process_string = string.replace('+','')
		final_string = process_string.split(/\s+/).join(' ').trim()
		for(e=0; e < special_characters.length; e++)
			final_string = final_string.replace(special_characters[e], ' ' + special_characters[e])	
		//Se filtran algunas acentuaciones previsoriamente
		with_tick = ['á','é','í','ó','ú']
		without_tick = ['a','e','i','o','u']
		for(e=0; e < with_tick.length; e++)
			final_string = final_string.replace(with_tick[e], without_tick[e])	
		return final_string
		//ej: 'hóla!' > 'hola !' 
}



function returnAnswer(answer_desc){
	/* search and return random answer with the same descriptcion 
		answer_desc:bienvenida -> random:[che, hola, ...]
	*/
	db = getKeys(DB_MBOT)
	for(i=0; i < db.length; i++){
		dbp = db[i].split('-')
		if(dbp[0] == 'respuesta' && dbp[1] == answer_desc){
			return randomItem(DB_MBOT[db[i]]);
		}
	}
}

function strStrSec(word0, word1){
	/* sequencial
		[holaaaa, hola] -> ho hol hola > hola
	*/
	word_buffer = []
	for(letter=0; letter < word0.length; letter++){
		word_buffer.push(word0[letter])
		if(word_buffer.join('') == word1)
			return true
	}
	return false
}

function strStr(words , string){
	/* comoooo estaasss? -> como estas?*/
	words_array = words.split(' ')
	string_array = string.split(' ')
	cout = 0
	if(words_array.length < string_array.length)
		return false
	for(i=0; i < string_array.length; i++){
		if(strStrSec(words_array[i], string_array[i]))
			cout++;
	}
	return cout
}


function dbSearchWord(word, indiceEspecifico=false){
	/*
		Searches for matches in the database of some specific word
	*/
	candidates = {}
	dbDir = indiceEspecifico ? getKeys(indiceEspecifico) : getKeys(DB_MBOT)
	for(key_pos=0; key_pos < dbDir.length; key_pos++){
		//Se entra por keys en la base de datos
		key_index = dbDir[key_pos] //key
		answers = DB_MBOT[key_index] //values
		if(answers != undefined){
			//escanea cada pregunta dentro de la lista
			for(answer_index=0; answer_index < answers.length; answer_index++){	
				if(key_index.split('-')[0] == 'respuesta') break
				answer = answers[answer_index]
				scan = strStr(word, answer)
				if(answer == word)
					candidates[key_index] = [key_index, answer_index, word]
				if(scan && scan == word.split(' ').length)
					candidates[key_index] = [key_index, answer_index, word]
			}
		}
	}
	if(Object.keys(candidates).length > 0)
		return candidates
	else
		return false
}

function mergeDict(from, to){
	/* Update/Extends dict from other dict */
	from_keys = getKeys(from)
	for(i=0; i<from_keys.length; i++){
		to[getKeys(to).length] = from[from_keys[i]]
	}
}

function analysisSentence(sentence){
	/*
		Look for several matches in a sentence and return dict with
		types.
	*/
	sentence = filterString(sentence).split(' ')
	sentence.push('\0')
	sentence_chunck = []
	last_analysis = false
	founds = {}
	word_count = 0;
	do {
		sentence_chunck.push(sentence[word_count])
		procString = filterString(sentence_chunck.join(' '))
		analysis = dbSearchWord(procString)
		if(!last_analysis){
			if(analysis)
				last_analysis = analysis
		}else{
			if(analysis){
				last_analysis = analysis
			}else{
				if(last_analysis){
					mergeDict(last_analysis, founds)
					sentence_chunck = []
					last_analysis = false
					word_count--;
				}
			}
		}

	}while(word_count++ < sentence.length)

	if(Object.keys(founds).length > 0)
		return founds
	else
		return {0:["error-null"]}

}

function procesarComando(comando){
	/*controla el sistema de comandos*/
	switch(comando){
		case '#clear':
			emptyMessageBox()
			console.clear()
			return '...';
		case '#olvidar':
			forgetConversation()
			return randomAnswer("pregunta-existencial")
		case '#DEBUG':
			if(DEBUG == false){
				DEBUG = true
				return "Depuracion Activada"
			}else{
				DEBUG = false
				return "Depuracion Desactivada"
		}
	}
}
function forgetConversation(){
	lobuloTemporal["ultimoMensaje"] = [];
}


//reply por un tipo de mensaje.
function processMessage(message){
	//itera sobre el mensaje, analiza, itera sobre el analisis y efectua
	sentence_analysis = analysisSentence(message)
	analysis_keys = getKeys(sentence_analysis)
	final_answer = []
	if(DEBUG){
		console.log("===================");
		console.log("Mensaje:", message)
		for(i=0;i < analysis_keys.length; i++){
			console.log("Analisis:", sentence_analysis[i])
		}
		
	}

	for(s_pos=0; s_pos < analysis_keys.length; s_pos++){
		sentence_key = sentence_analysis[s_pos][0]
		key_info = sentence_key.split("-")
		sentence_type = key_info[0]
		sentence_info = key_info[1]
		//Revisar si el usuario ya dijo la misma cosa consecutivamente (por tipo de expresion)
		if(lobuloTemporal["ultimoMensaje"].join('').includes(sentence_key)){
			final_answer.push(randomAnswer('respuesta-repeticion'))
			forgetConversation()
		}else{
			forgetConversation();
		}
		lobuloTemporal['ultimoMensaje'].push(sentence_key)
		
		//controlar funciones especiales
		switch(sentence_type){
			case 'saludo':
				final_answer.push(randomAnswer('saludo-'+sentence_info))
				break
			case 'error':
				lobuloTemporal['conteoError']++;
				if(lobuloTemporal['conteoError'] > 4){
					lobuloTemporal['conteoError'] = 0;
					return randomAnswer('respuesta-discusion')
				}else{
					return randomAnswer('respuesta-desconocido')
				}
			case 'accion':
				switch(sentence_info){
					case 'comando':
						return procesarComando(message)
					case 'hora':
						hora = new Date()
						return returnAnswer(sentence_info) + hora.getHours() + " y " + hora.getMinutes() + " minutos."
					case 'buscar':
						queryBusqueda = "search?q="
						key = analisis[s_pos][0]
						posicion = analisis[s_pos][1]
						itemBuscar = filterString(message.replace(DB_MBOT[key][posicion], ''))
						console.log(window.location.href)
						if(window.location.href.toString().includes(queryBusqueda))
							window.location.href = window.location.href + itemBuscar
						else
							window.location.href = window.location.href + queryBusqueda + itemBuscar
						break;
					case 'quitar':
						window.location.href = "https://www.google.com"
						return randomAnswer('saludo-despedida')
				}
				return randomAnswer('respuesta-afirmacion de accion')
			
			default: //respuesta por defecto
				respuesta = returnAnswer(sentence_info)
				if(respuesta){
					final_answer.push(respuesta)
				}else{
					final_answer.push(randomAnswer('respuesta-desconocido'))
				}
		}
	}
	console.log("=>>", final_answer)
	mensaje = filterString(final_answer.join(', '))
	mensaje = mensaje[0].toUpperCase() + mensaje.substr(1) + '.'
	return mensaje
}

//Añadir un mensaje en la caja de conversacion.
function addMessageIntoBox(nombre, color, mensaje, emoji="em em-no_mouth"){
	nombre = ''//"<span style='position:relative;color:" + color + "'>" + nombre + " </span>"
	mensaje = "<span>" + mensaje +"</span>"
	emoji = 		 "<div style='display: inline-block;' class='"+ emoji +"'></div>"
	mensajeFormato = "<div style='display: inline-block;width:200px' id='mensaje'>"+ nombre + mensaje + "</div>"
	msj = document.createElement("div")
	msj.innerHTML = emoji
	msj.innerHTML += mensajeFormato
	msj.className = "mensajeAnimacion"
	messageBox.appendChild(msj)
}

//Vaciar la caja de conversacion.
function emptyMessageBox(){
		messageBox.innerHTML = ''
}

//Manejar un intervalo de inactividad para enviar un mensaje automatico
var silenceInterval = setInterval(function(){reply()}, mutedTime);

//reply un Mensaje y Devolver una Respuesta (Funcion principal)
function reply(){
		var userMessages = userInputBox.value.toLowerCase();
		//Si la cantidad de mensajes excede al limite de la caja se limpia.
		if(actualMessageAmount > maxMessageBox){
			emptyMessageBox()
			actualMessageAmount=0
		}
		
		//El usuario ya dijo algo, no hay necesidad de llamar mas la atención.
		window.clearInterval(silenceInterval)
		//Se agrega el mensaje del usuario a la caja de conversación.
		if(userMessages!='')
			addMessageIntoBox('Usuario', 'purple', userInputBox.value, emoji="em em-smiley")
		else
			userMessages = '*silencio*';
		typingNotification.innerHTML = "Escribiendo..";
		setTimeout(function(){
						//Se muestra la notificacion simulada de escritura.
						typingNotification.innerHTML = "...";
						addMessageIntoBox('MinBot', 'red', processMessage(userMessages), emoji="em em-robot_face")
					 }, 
					  responseTime)
		actualMessageAmount++;
	
}
