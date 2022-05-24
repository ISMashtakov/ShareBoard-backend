from unittest import TestCase

from file_manager.operations import Insert, Delete, NeutralOperation


class InsertInsertTestCase(TestCase):
    def setUp(self) -> None:
        self.text = "Michael Scofield"

    def test_insert_before(self):
        prev_insert = Insert(8, "J. ")
        current_text = prev_insert.execute(self.text)
        current_insert = Insert(0, "origami ")
        current_text = (current_insert / prev_insert).execute(current_text)
        self.assertEqual(current_text, "origami Michael J. Scofield")

    def test_insert_to_same_position(self):
        prev_insert = Insert(0, "ami ")
        current_text = prev_insert.execute(self.text)
        current_insert = Insert(0, "orig")
        current_text = (current_insert / prev_insert).execute(current_text)
        self.assertEqual(current_text, "origami Michael Scofield")

    def test_insert_after(self):
        prev_insert = Insert(0, "origami ")
        current_text = prev_insert.execute(self.text)
        current_insert = Insert(8, "J. ")
        current_text = (current_insert / prev_insert).execute(current_text)
        self.assertEqual(current_text, "origami Michael J. Scofield")

    def test_prev_and_current_insert_are_equal(self):
        prev_insert = Insert(0, "origami ")
        current_text = prev_insert.execute(self.text)
        current_insert = Insert(0, "origami ")
        current_text = (current_insert / prev_insert).execute(current_text)
        self.assertEqual(current_text, "origami origami Michael Scofield")


class InsertDeleteTestCase(TestCase):
    def setUp(self) -> None:
        self.text = "Michael Scofield"

    def test_insert_before_delete_segment(self):
        prev_delete = Delete(4, "ael")
        current_text = prev_delete.execute(self.text)
        current_insert = Insert(0, "J. ")
        current_text = (current_insert / prev_delete).execute(current_text)
        self.assertEqual(current_text, "J. Mich Scofield")

    def test_insert_the_same_position(self):
        prev_delete = Delete(0, "Michael")
        current_text = prev_delete.execute(self.text)
        current_insert = Insert(0, "Michael")
        current_text = (current_insert / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Michael Scofield")

    def test_insert_in_delete_segment(self):
        prev_delete = Delete(0, "Michael")
        current_text = prev_delete.execute(self.text)
        current_insert = Insert(3, "key")
        current_text = (current_insert / prev_delete).execute(current_text)
        self.assertEqual(current_text, "key Scofield")

    def test_insert_at_the_end_of_delete_segment(self):
        prev_delete = Delete(0, "Michael ")
        current_text = prev_delete.execute(self.text)
        current_insert = Insert(8, "J. ")
        current_text = (current_insert / prev_delete).execute(current_text)
        self.assertEqual(current_text, "J. Scofield")

    def test_insert_after_delete_segment(self):
        prev_delete = Delete(0, "Mich")
        current_text = prev_delete.execute(self.text)
        current_insert = Insert(8, "J. ")
        current_text = (current_insert / prev_delete).execute(current_text)
        self.assertEqual(current_text, "ael J. Scofield")


class DeleteDeleteTestCase(TestCase):
    def setUp(self) -> None:
        self.text = "Michael Scofield"

    def test_delete_before(self):
        prev_delete = Delete(3, "hael ")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(0, "Mic")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_right_border_in_prev_delete(self):
        prev_delete = Delete(3, "hael ")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(0, "Micha")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_before_right_border_in_prev_delete_border_value(self):
        prev_delete = Delete(3, "hael ")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(0, "Mich")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_in_prev_delete_segment(self):
        prev_delete = Delete(0, "Michael ")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(3, "ha")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_in_prev_delete_segment_left_border_value(self):
        prev_delete = Delete(3, "hae")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(3, "hael")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Mic Scofield")

    def test_delete_in_prev_delete_segment_right_border_value(self):
        prev_delete = Delete(3, "hael")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(0, "Michael")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, " Scofield")

    def test_prev_and_current_delete_are_equal(self):
        prev_delete = Delete(3, "h")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(3, "h")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Micael Scofield")

    def test_delete_left_border_in_prev_delete(self):
        prev_delete = Delete(0, "Michae")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(3, "hael ")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_left_border_in_prev_delete_left_border_value(self):
        prev_delete = Delete(0, "Mich")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(0, "Michael ")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_left_border_in_prev_delete_right_border_value(self):
        prev_delete = Delete(6, "l ")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(0, "Michael")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_at_the_end_of_prev_delete(self):
        prev_delete = Delete(0, "Michael")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(7, " ")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_delete_after_prev_delete(self):
        prev_delete = Delete(0, "Michael")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(8, "Scofield")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, " ")

    def test_prev_delete_in_current_delete(self):
        prev_delete = Delete(3, "hae")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(0, "Michael")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, " Scofield")

    def test_prev_delete_in_current_delete_left_border_value(self):
        prev_delete = Delete(3, "hael")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(3, "hae")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Mic Scofield")

    def test_prev_delete_in_current_delete_right_border_value(self):
        prev_delete = Delete(0, "Michael")
        current_text = prev_delete.execute(self.text)
        current_delete = Delete(3, "hael")
        current_text = (current_delete / prev_delete).execute(current_text)
        self.assertEqual(current_text, " Scofield")


class DeleteInsertTestCase(TestCase):
    def setUp(self) -> None:
        self.text = "Michael Scofield"

    def test_delete_before_insert(self):
        prev_insert = Insert(3, "key")
        current_text = prev_insert.execute(self.text)
        current_delete = Delete(1, "ic")
        current_text = (current_delete / prev_insert).execute(current_text)
        self.assertEqual(current_text, "Mkeyhael Scofield")

    def test_delete_before_insert_border_value(self):
        prev_insert = Insert(7, "J.")
        current_text = prev_insert.execute(self.text)
        current_delete = Delete(0, "Michael")
        current_text = (current_delete / prev_insert).execute(current_text)
        self.assertEqual(current_text, "J. Scofield")

    def test_delete_left_border_in_insert(self):
        prev_insert = Insert(8, "J. ")
        current_text = prev_insert.execute(self.text)
        current_delete = Delete(8, "Sco")
        current_text = (current_delete / prev_insert).execute(current_text)
        self.assertEqual(current_text, "Michael J. field")

    def test_delete_after_insert(self):
        prev_insert = Insert(0, "o ")
        current_text = prev_insert.execute(self.text)
        current_delete = Delete(8, "Sco")
        current_text = (current_delete / prev_insert).execute(current_text)
        self.assertEqual(current_text, "o Michael field")

    def test_insert_in_delete_segment(self):
        prev_insert = Insert(3, "key")
        current_text = prev_insert.execute(self.text)
        current_delete = Delete(1, "ichael")
        current_text = (current_delete / prev_insert).execute(current_text)
        self.assertEqual(current_text, "M Scofield")

    def test_insert_in_delete_segment_left_border_value(self):
        prev_insert = Insert(1, "key")
        current_text = prev_insert.execute(self.text)
        current_delete = Delete(1, "ichael")
        current_text = (current_delete / prev_insert).execute(current_text)
        self.assertEqual(current_text, "Mkey Scofield")

    def test_insert_in_delete_segment_right_border_value(self):
        prev_insert = Insert(7, "key")
        current_text = prev_insert.execute(self.text)
        current_delete = Delete(1, "ichael")
        current_text = (current_delete / prev_insert).execute(current_text)
        self.assertEqual(current_text, "Mkey Scofield")


class NeutralOperationTestCase(TestCase):
    def setUp(self) -> None:
        self.text = "Michael Scofield"

    def test_insert_after_neu(self):
        prev_neu = NeutralOperation()
        current_text = prev_neu.execute(self.text)
        current_insert = Insert(8, "J. ")
        current_text = (current_insert / prev_neu).execute(current_text)
        self.assertEqual(current_text, "Michael J. Scofield")

    def test_delete_after_neu(self):
        prev_neu = NeutralOperation()
        current_text = prev_neu.execute(self.text)
        current_delete = Delete(0, "Michael ")
        current_text = (current_delete / prev_neu).execute(current_text)
        self.assertEqual(current_text, "Scofield")

    def test_neu_after_neu(self):
        prev_neu = NeutralOperation()
        current_text = prev_neu.execute(self.text)
        current_neu = NeutralOperation()
        current_text = (current_neu / prev_neu).execute(current_text)
        self.assertEqual(current_text, "Michael Scofield")

    def test_neu_after_insert(self):
        prev_insert = Insert(0, 'oh, ')
        current_text = prev_insert.execute(self.text)
        current_neu = NeutralOperation()
        current_text = (current_neu / prev_insert).execute(current_text)
        self.assertEqual(current_text, "oh, Michael Scofield")

    def test_neu_after_delete(self):
        prev_delete = Delete(0, 'Michael ')
        current_text = prev_delete.execute(self.text)
        current_neu = NeutralOperation()
        current_text = (current_neu / prev_delete).execute(current_text)
        self.assertEqual(current_text, "Scofield")
