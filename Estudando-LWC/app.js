//Source: https://developer.mozilla.org/pt-BR/docs/Web/JavaScript/Reference/Global_Objects/String
//console.log("Bem Vindo ao Log");

//console.error("Eu sou um erro");

//console.warn("Aviso");

//comentando do JS

/* é igual no apex 
abre lá, e fecha aqui */

//console.log("Aqui NÃO ESTÁ COMENTANDO MAIS");

//Add Datatypes 04/12/2022
/*const sobreNome = 'Parise Garpelli'
const numeroCPF = 42209887852
const brasileiro = true
const numeroVazio = null

console.log(sobreNome,':', numeroCPF,':', brasileiro);
console.log(typeof sobreNome, typeof numeroCPF, typeof brasileiro);*/

//Source: https://developer.mozilla.org/pt-BR/docs/Web/JavaScript/Reference/Global_Objects/Array

//Adicionando itens a uma lista (comando push)
const listaNum = [10,12,13,14,15,16,17,18,19]
console.log(listaNum);

listaNum.push(125);
console.log(listaNum);

//trocando o item da lista
listaNum[1] = (11);
console.log(listaNum);

//Pegando apenas um trecho da lista (items 0~4)
console.log(listaNum.slice(0,4));
