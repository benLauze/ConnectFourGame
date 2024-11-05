#-*- coding: utf-8 -*-
"""
Created on Fri Oct 27 15:27:43 2023

@author: Benjamin Lauze
"""

import socket
import threading
import random
import json

lock = threading.Lock()

class ConnectFourGameSession:
    def __init__(self, password, player1):
        self.password = password
        self.players = [player1, None]
        self.game_board = [[0 for _ in range(7)] for _ in range(6)]
        self.game_active = False  # Indicates whether the game is active
        self.game_session_active = False
        
    def add_player(self, player2_socket):
        if self.players[1] is None:
            self.players[1] = player2_socket
            return True  
        else:
            return False 
        
        
    def activateGame(self):
        lock.acquire()
        
        self.game_active = True
        self.game_session_active = True
        # Notify both players that the game has started
        
        current_player = self.players[0]
        symbol = 1 # PLAYER 1
        
        while self.game_active:
            print(self.game_board)
            board_json = json.dumps(self.game_board)
            current_player.sendall(f"YOUR_TURN {board_json}".encode())
            
            # PLAYER SWAP VIA IF STATEMENT
            other_player = self.players[1] if current_player == self.players[0] else self.players[0]       
            other_player.sendall(f"WAITING_TURN {board_json}".encode())        
            
            # SYMBOL SWAP VIA IF STATEMENT
            symbol = 2 if current_player == self.players[1] else 1
            
            print("Waiting to recv")
            while True:
                try:
                    move = current_player.recv(2048).decode()
                    print("Got move from player")
                    break
                except Exception as e:
                    pass
            
            move = move.split()    
            current_move = int (move[1])
            
            print("Move from player", move)
            self.moves(current_move,symbol)
            
            current_player = other_player
        board_json = json.dumps(self.game_board)    
        winnerSocket = f"HOST_PLAYER_WON {self.game_board}" if current_player == self.players[1] else f"JOINING_PLAYER_WON {self.game_board}"
        
        self.players[0].sendall(f"{winnerSocket}".encode()) 
        self.players[1].sendall(f"{winnerSocket}".encode()) 
        
        
#Taken out due to odd results
        """
        while True:
            try:
                player1_response = self.players[0].recv(2048).decode()
                player2_response = self.players[1].recv(2048).decode()  
                print("recieved responses")
                break
            
            except Exception as e:
                pass
            
        
        print("reaches end sequence response")
        
        if player1_response == "AGAIN_ACCEPTED" and player2_response == "AGAIN_ACCEPTED":
             print("again accpted")
             self.game_board = [[0 for _ in range(7)] for _ in range(6)] 
             self.players[0].sendall("RESET".encode())
             self.players[1].sendall("RESET".encode()) 
             self.activateGame()
        else:
             print("forced cancel")
             self.players[0].sendall("FORCED_CANCEL".encode()) 
             self.players[1].sendall("FORCED_CANCEL".encode()) 
             self.game_session_active = False
             self.remove_game()
        """
        self.game_session_active = False
        
        
    def remove_game(self, game):
        if game in self.active_games:
            self.active_games.remove(game)
                
    def moves(self, column, symbol):
        
        for row in range(len(self.game_board) - 1, -1, -1):           
            if self.game_board[row][column] == 0:
                self.game_board[row][column] = symbol
                currentWinCheck = self.winCheck()
                if currentWinCheck is not None:
                    print("wincheck hit", currentWinCheck)
                    self.print_board(self.game_board)
                    self.game_active = False
                     
                break
        return 

    def print_board(self,board):
        for row in board:
            print(" ".join(str(cell) for cell in row))
    
    
    def winCheck(self):
        
       for symbol in [1,2]:
            # Check horizontal lines
           for row in self.game_board:
               for col in range(4):
                   if row[col] == row[col + 1] == row[col + 2] == row[col + 3] == symbol:
                       print("H hit")
                       return symbol
    
           # Check vertical lines
           for col in range(7):
               for row in range(3):
                   if ( self.game_board[row][col] == self.game_board[row + 1][col] == 
                       self.game_board[row + 2][col] == self.game_board[row + 3][col] == symbol):
                       print("V hit")
                       return symbol
    
           # Check diagonal (down-right and up-right)
           for col in range(4):
               for row in range(6):
                   # Down-right
                   if (row < 3 and self.game_board[row][col] == 
                       self.game_board[row + 1][col + 1] == 
                       self.game_board[row + 2][col + 2] == 
                       self.game_board[row + 3][col + 3] == symbol ):
                       print("D hit")

                       return symbol
                   # Up-right
                   if ( row > 2 and self.game_board[row][col] == 
                        self.game_board[row - 1][col + 1] == 
                        self.game_board[row - 2][col + 2] ==
                        self.game_board[row - 3][col + 3] == symbol):
                       print("D hit")

                       return symbol
    
       # No winner yet
       return None
          
                
    
        
class ConnectFourServer:
    
    def __init__(self,port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setblocking(0)
        self.port = port
        self.s.bind(('', self.port))
        self.s.listen(30)
        self.activeGames = []
        
        # Server main loop
    def start(self):
        print("Server side")
        while True:
            try:
                clientsocket, address = self.s.accept()
                print("New connection from client", address)
                newThread = threading.Thread(target=self.clientThread, args=(clientsocket, address))
                newThread.start()
            except:
                pass
    
        
    def startGame(self, clientsocket):
        password = random.randint(1000, 9999)
        while self.passwordInUse(password):
            password = random.randint(1000, 9999)

        newGame = ConnectFourGameSession(password, clientsocket)
        self.activeGames.append(newGame)
        clientsocket.sendall(str(password).encode())
        print("Started new game with password", password)
        
    def passwordInUse(self, password):
       for game in self.activeGames:
            if password == game.password:
                return True
       return False    
        
    
    def player_joined(self, player):
        return True if player != None else False
    
    def password(self, clientsocket,password):
        try:
            for game in self.activeGames:
                print(f"game.password: {type(game.password)} - {game.password}")
                print(f"password: {type(password)} - {password}")     
                print(f"Matching: {game.password == int(password)}")
                
                if game.password == password: 
                    if game.add_player(clientsocket):
                        clientsocket.sendall("PASSWORD_ACCEPTED".encode())
                        game.players[0].sendall("PASSWORD_ACCEPTED".encode())
                        if(self.player_joined(game.players[1])):
                            game.activateGame()

                        return 
                    else:
                        clientsocket.sendall("Game is full.".encode())
                        return 
            clientsocket.sendall("Invalid password.".encode())
        except Exception as e:
            print(e)
            clientsocket.sendall("Illegal password, please try again.".encode())
    
    
    def exitGame(self, clientsocket):
        clientsocket.close() 
        print(f"Closed Connection with client: {clientsocket}")
        self.newThread.close()
    
    
    def respond(self,clientsocket, address, clientData):
        """
        Supported commands [WIP]:
            STARTGAME
            PASSWORD [passwrd]
            EXITGAME
            AGAIN
            PLAYABLE MOVES [0 - 6]
        """
       
        commandData = clientData.split()
        command = commandData[0]
        
        match command:
            case "STARTGAME":
                self.startGame(clientsocket)
            case "PASSWORD":
                password = commandData[1]
                password.strip()
                self.password(clientsocket, int(password))
            case "EXITGAME":
                self.exitGame(clientsocket)
            case "AGAIN":
                self.again(clientsocket)
                
    
        # Individual thread spawned for each connected client
    def clientThread(self, clientsocket, address):
        while True:
            if len(self.activeGames) != 0:
                
                for game in self.activeGames:
                    if game.players[0] == clientsocket or game.players[1] == clientsocket:
                        break
                    
                if game.game_session_active :
                    
                    continue
           
            try:
               # print("Recvd from client socked")
                message = clientsocket.recv(2048).decode()
                if not message:
                    continue  # No more data received, exit the loop and thread
                print("Got message from client", message)
                self.respond(clientsocket, address, message)
            except Exception as e:
                pass
               # print(f"Error: {e}. Socket has been closed closing thread")                
               # break  # Socket likely closed, exit the loop and thread

            


                            
if __name__ == "__main__":
    server = ConnectFourServer(1234)
    server.start()