import random
from django.test import TestCase, Client
from board.models import User, Board

# Create your tests here.
class BoardTests(TestCase):
    # Initializer
    def setUp(self):
        alice = User.objects.create(name="Alice")
        Board.objects.create(user=alice, board_state="1"*2500, board_name="alice's board")

    # Utility functions
    def post_board(self, board_state, board_name, user_name):
        payload = {
            "board": board_state,
            "boardName": board_name,
            "userName": user_name
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}
        return self.client.post("/boards", data=payload, content_type="application/json")

    def get_board(self):
        return self.client.get("/boards")

    def get_board_index(self, index):
        return self.client.get(f"/boards/{index}")
    
    def delete_board_index(self, index):
        return self.client.delete(f"/boards/{index}")
    
    def put_board_index(self, index, board_state, board_name, user_name):
        payload = {
            "board": board_state,
            "boardName": board_name,
            "userName": user_name
        }
        
        payload = {k: v for k, v in payload.items() if v is not None}
        
        return self.client.put(f"/boards/{index}", data=payload, content_type="application/json")


    # Now start testcases.    
    def test_add_board(self):       
        random.seed(1) 
        for _ in range(50):
            board_state = ''.join([random.choice("01") for _ in range(2500)])
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
            user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
            res = self.post_board(board_state, board_name, user_name)
            
            self.assertJSONEqual(res.content, {"code": 0, "info": "Succeed", "isCreate": True})
            self.assertTrue(User.objects.filter(name=user_name).exists())
            self.assertTrue(Board.objects.filter(board_name=board_name, board_state=board_state).exists())
    
    
    def test_add_board_twice(self):
        random.seed(1) 
        for _ in range(50):
            board_state = ''.join([random.choice("01") for _ in range(2500)])
            board_state_2 = ''.join([random.choice("01") for _ in range(2500)])
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
            user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
            res = self.post_board(board_state, board_name, user_name)
            res = self.post_board(board_state_2, board_name, user_name)
            
            self.assertJSONEqual(res.content, {"code": 0, "info": "Succeed", "isCreate": False})
            self.assertTrue(User.objects.filter(name=user_name).exists())
            self.assertFalse(Board.objects.filter(board_name=board_name, board_state=board_state).exists())
            self.assertTrue(Board.objects.filter(board_name=board_name, board_state=board_state_2).exists())
    
    
    # `board` key missing
    def test_add_board_without_board(self):
        random.seed(2)
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
        res = self.post_board(None, board_name, user_name)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(User.objects.filter(name=user_name).exists())
        self.assertFalse(Board.objects.filter(board_name=board_name).exists())
    
    
    # + board key length incorrect
    def test_add_board_state_length_incorrect(self):
        random.seed(3)
        for _ in range(50):
            length = random.randint(0, 2499)
            
            board_state = ''.join([random.choice("01") for _ in range(length)])
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
            user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
            res = self.post_board(board_state, board_name, user_name)
            
            self.assertNotEqual(res.json()['code'], 0)
            self.assertNotEqual(res.status_code, 200)
            self.assertFalse(User.objects.filter(name=user_name).exists())
            self.assertFalse(Board.objects.filter(board_name=board_name).exists())
    
    
    # + board with invalid char
    def test_add_board_state_invalid_char(self):
        random.seed(4)
        for _ in range(50):
            
            board_state = ''.join([random.choice("0123") for _ in range(2500)])
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
            user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
            res = self.post_board(board_state, board_name, user_name)
            
            self.assertNotEqual(res.json()['code'], 0)
            self.assertNotEqual(res.status_code, 200)
            self.assertFalse(User.objects.filter(name=user_name).exists())
            self.assertFalse(Board.objects.filter(board_name=board_name).exists())
        
        for _ in range(50):
            board_state = ''.join(random.choice("01中文测试") for _ in range(2500))
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
            user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
            res = self.post_board(board_state, board_name, user_name)
            
            self.assertNotEqual(res.json()['code'], 0)
            self.assertNotEqual(res.status_code, 200)
            self.assertFalse(User.objects.filter(name=user_name).exists())
            self.assertFalse(Board.objects.filter(board_name=board_name).exists())
        
        
    # + boardName key missing
    def test_add_board_without_board_name(self):
        random.seed(5)
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
        res = self.post_board(board_state, None, user_name)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(User.objects.filter(name=user_name).exists())
        self.assertFalse(Board.objects.filter(board_state=board_state).exists())


    # + boardName key length incorrect
    def test_add_board_boardname_length(self):
        random.seed(6)
        for length in [0, 51, 255]:
            board_state = ''.join([random.choice("01") for _ in range(2500)])
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(length)])
            user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
            res = self.post_board(board_state, board_name, user_name)
            
            self.assertNotEqual(res.json()['code'], 0)
            self.assertNotEqual(res.status_code, 200)
            self.assertFalse(User.objects.filter(name=user_name).exists())
            self.assertFalse(Board.objects.filter(board_state=board_state).exists())


    # + userName key missing
    def test_add_board_username_missing(self):
        random.seed(7)
        board_state = ''.join([random.choice("01") for _ in range(2500)])
        board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
        user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
        res = self.post_board(board_state, board_name, None)
        
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        self.assertFalse(User.objects.filter(name=user_name).exists())
        self.assertFalse(Board.objects.filter(board_state=board_state).exists())
            
            
    # + userName key points to existing user
    def test_add_board_username_exists(self):
        random.seed(8)
        user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])

        for _ in range(10):
            board_state = ''.join([random.choice("01") for _ in range(2500)])
            board_name = ''.join([random.choice("qwertyuiop12345678") for _ in range(50)])
            # user_name = ''.join([random.choice("asdfghjkl12345678") for _ in range(50)])
            res = self.post_board(board_state, board_name, user_name)
            
            self.assertEqual(res.json()['code'], 0)
            self.assertEqual(res.status_code, 200)

        user = User.objects.filter(name=user_name).first()
        self.assertGreaterEqual(len(Board.objects.filter(user=user)), 10)
            
            
    # + normal case [GET]
    def test_get_boards(self):
        random.seed(9)
        res = self.get_board()
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 200)
        
        
    # + unsupported method
    def test_delete_boards(self):
        res = self.client.delete("/boards")
        self.assertEqual(res.json()['code'], -3)
        self.assertEqual(res.status_code, 405)
    
    
    # /boards/<index>
    # GET
    # + normal case
    def test_boards_index_get(self):
        index = 1
        res = self.get_board_index(index)
        self.assertEqual(res.json()['code'] , 0)
        self.assertJSONEqual(res.content, {'code': 0, 'info': 'Succeed', 'board': '1'*2500, 'boardName': "alice's board", 'userName': 'Alice'})
        self.assertEqual(res.status_code, 200)
    
    
    # + index not int
    def test_boards_index_get_idx(self):
        index = "aaa"
        res = self.get_board_index(index)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)


    # + do not exist
    def test_boards_index_get_do_not_exist(self):
        index = 2
        res = self.get_board_index(index)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 404)


    # DELETE
    # + normal case
    def test_boards_index_delete_do_not_exist(self):
        index = 1
        res = self.delete_board_index(index)
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(Board.objects.all()), 0)
        
    # + index not int
    def test_boards_index_delete_do_not_exist2(self):
        index = "aaa"
        res = self.delete_board_index(index)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        
    # + do not exist
    def test_boards_index_delete_do_not_exist3(self):
        index = 2
        res = self.delete_board_index(index)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 404)


    # PUT
    # + normal case
    def test_boards_index_put(self):
        index = 1
        
        board_state = "01" * 1250
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, board_state, board_name, user_name)
        
        self.assertEqual(res.json()['code'], 0)
        self.assertEqual(res.json()['info'], "Succeed")
        self.assertTrue('isCreate' not in res.json())
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Board.objects.filter(id=1).first().board_state, board_state)
        self.assertEqual(Board.objects.filter(id=1).first().board_name, board_name)
        self.assertEqual(Board.objects.filter(id=1).first().user, User.objects.filter(name=user_name).first())

    # + index not int
    def test_boards_index_put1(self):
        index = "aaa"
        
        board_state = "01" * 1250
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, board_state, board_name, user_name)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)

    # + do not exist
    def test_boards_index_put2(self):
        index = 2
        
        board_state = "01" * 1250
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, board_state, board_name, user_name)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertEqual(res.status_code, 404)
        

    # + board key missing
    def test_boards_index_put3(self):
        index = 1
        
        board_state = "01" * 1250
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, None, board_name, user_name)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)

    # + board key length incorrect
    def test_boards_index_put4(self):
        index = 1
        
        board_state = "01" * 1249
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, board_state, board_name, user_name)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        
    # + board with invalid char
    def test_boards_index_put5(self):
        index = 1
        
        board_state = "0123" * 625
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, board_state, board_name, user_name)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)

    # + boardName key missing
    def test_boards_index_put6(self):
        index = 1
        
        board_state = "01" * 1250
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, board_state, None, user_name)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)
        
        
    # + userName key missing
    def test_boards_index_put7(self):
        index = 1
        
        board_state = "01" * 1250
        board_name = "changed_board"
        user_name = "Bob"
        
        res = self.put_board_index(index, board_state, board_name, None)
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)

    # + unique constraint
    def test_boards_index_put8(self):
        _ = self.post_board("01" * 1250, "board1", "Alice")
        res = self.put_board_index(1, "01" * 1250, "board1", "Alice")
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)


    # + unsupported method
    def test_boards_index_unsupported(self):
        index = 1
        
        res = self.client.post(f"/boards/{index}")
        self.assertNotEqual(res.json()['code'], 0)
        self.assertNotEqual(res.status_code, 200)


    ### Testcases for user_board
    def test_user_board(self):
        res = self.client.get(f"/user/Alice")
        self.assertEqual(res.status_code, 200)
        self.assertGreater(len(res.json()['boards']), 0)
        self.assertFalse("board" in res.json()['boards'][0])
    
    
    def test_delete_user_board(self):
        res = self.client.delete(f"/user/Alice")
        alice = User.objects.filter(name="Alice").first()
        self.assertTrue(alice is not None)
        self.assertEqual(Board.objects.filter(user=alice).count(), 0)
