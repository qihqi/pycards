port module Main exposing (main)

import Set exposing (Set, insert, remove)
import Array
import Browser
import Debug
import Html exposing (Html, button, div, text, h4, h3, h4, hr, span, input, form, img, p)
import Html.Events exposing (onClick, on, onInput, onCheck)
import Html.Attributes exposing (class, id, style, attribute, name, value, type_, placeholder, checked)
import String

import Json.Encode as Encode
import Json.Decode as Decode exposing (Decoder, int, string, list, maybe, field, andThen)
import Json.Decode.Pipeline exposing (required, optional)


port sendMessage : String -> Cmd msg
port messageReceiver: (String -> msg) -> Sub msg

type GameStatus = Start | PLAYING

type alias Player = 
  { name : String
  , score: Int
  }

decodePlayer : Decoder Player
decodePlayer =
  Decode.succeed Player 
    |> required "name" string
    |> required "score" int

type alias Game = 
    { table :  List (String, List Int)
    , deck_count : Int
    }

decodeTuple = 
  Decode.map2 Tuple.pair
    (Decode.index 0 string)
    (Decode.index 1 (list int))

decodeGame : Decoder Game
decodeGame =
  Decode.succeed Game
    |> required "table" (list decodeTuple)
    |> required "score" int


type alias Room =
    { game : Maybe Game
    , players : List Player
    , observers : List Player
    , current_player : Maybe Player
    } 

decodeRoom =
  Decode.succeed Room
   |> optional "game" (maybe decodeGame) Nothing
   |> required "players" (list decodePlayer)
   |> required "observers" (list decodePlayer)
   |> optional "current_player" (maybe decodePlayer) Nothing


type alias Model = 
    { room: Room 
    , status: GameStatus 
    , auto_end_turn: Bool
    , hand: List Int
    , my_name: String
    , my_team: String
    , messages: List String
    , draft: String
    , table_selected: Set Int
    , hand_selected: Set Int
    }

decodeHand = list int

initialTable : (String, List Int)
initialTable = ("hand", [2,3,4])


init_state : () -> (Model, Cmd msg)
init_state _ = 
    ( { room =
            { game = Just { table=[initialTable], deck_count=54}
            , players = [{name = "han", score=12}]
            , observers = []
            , current_player = (Just {name = "han", score=12})
            }
        , status = Start
        , auto_end_turn = False
        , hand = [0]
        , my_name = "han"
        , my_team = ""
        , messages = []
        , draft = ""
        , hand_selected = Set.empty
        , table_selected = Set.empty
        }
        , Cmd.none
    )


main = 
    Browser.element 
      { init =init_state
      , update = update
      , view = view
      , subscriptions = subscriptions 
      }

type Msg =
    SetState String 
    | UI UIAction
    | TableSelect Int Bool
    | HandSelect Int Bool
    | Send 
    | DraftChanged String 
    | MessageReceived String
    | Incoming String 
    | None

type UIAction =
    DRAW | PLAY | TAKE_BACK | RETURN_TO_DECK |
    CLEAR_TABLE | END_TURN | TAKE_TURN | REFRESH


update : Msg -> Model -> (Model, Cmd Msg)
update msg model = 
  case msg of
    SetState x -> 
      ({ model | 
          room = 
             case Decode.decodeString (field "room" decodeRoom) x of 
               Ok r -> r
               Err e -> model.room 
       ,  hand = case Decode.decodeString (field "hand" decodeHand) x of
               Ok r -> r
               Err e -> model.hand
       }
       , Cmd.none)

    MessageReceived m -> ({model | messages = model.messages ++ [m] }, Cmd.none)

    Send -> ({model | draft = ""}, sendMessage (makeChatMessage model.my_name model.draft))

    DraftChanged m -> ({model | draft = m}, Cmd.none)

    HandSelect cardId isAdd -> 
      ( { model | hand_selected = 
           if isAdd 
              then (insert cardId model.hand_selected)
              else (remove cardId model.hand_selected)
        }
        , Cmd.none
      )

    TableSelect cardId isAdd -> 
      ( { model | table_selected = 
           if isAdd 
              then (insert cardId model.table_selected)
              else (remove cardId model.table_selected)
        }
        , Cmd.none
      )

    UI action -> (model, makeAction action model |> sendMessage)
    Incoming message -> 
        ( case (Decode.decodeString (execAction model) message) of
            Ok m -> m
            Err e -> Debug.log (Decode.errorToString e) model
        , Cmd.none
        )
    _ -> (model, Cmd.none)
      

makeAction : UIAction -> Model -> String
makeAction action model =
  let msg = case action of 
        DRAW -> 
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "DRAW")
            , ("arg", Encode.object [("num_cards", Encode.int 1)])
            ]
        PLAY -> 
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "PLAY")
            , ("arg", Encode.object 
                [ ("cards", Encode.list Encode.int (Set.toList model.hand_selected)) ])
            ] 
            
        TAKE_BACK ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "TAKE_BACK")
            , ("arg", Encode.object 
                [ ("cards", Encode.list Encode.int (Set.toList model.table_selected)) ])
            ] 
        RETURN_TO_DECK ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "RETURN_TO_DECK")
            , ("arg", Encode.object 
                [ ("cards", Encode.list Encode.int (Set.toList model.hand_selected)) ])
            ] 
        CLEAR_TABLE ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "CLEAR_TABLE")
            , ("arg", Encode.string "")
            ] 
        END_TURN ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "END_TURN")
            , ("arg", Encode.string "")
            ] 
        TAKE_TURN ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "TAKE_TURN")
            , ("arg", Encode.string "")
            ] 
        REFRESH ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "GET_STATE")
            , ("arg", Encode.string "")
            ] 
  in Encode.encode 0 msg

makeChatMessage my_name message =
  Encode.encode 0 (Encode.object 
            [ ("name", Encode.string my_name)
            , ("action", Encode.string "MESSAGE")
            , ("arg", Encode.string message)
            ] )

view model  = 
  case model.room.game of
    Nothing -> div [][]
    Just game ->
        let 
          turnText = 
              case model.room.current_player of
                Nothing -> ""
                Just p -> if p.name == model.my_name then 
                      "YOUR TURN"
                    else
                      p.name ++ "'s turn" 
        in 
            div []
            [ div [ id "chat_area"] 
                  [  h3 [] [text "hello"]
                  ,  div [id "chat_text"] 
                         (List.map (\x -> p [] [text x]) model.messages)
                  ,  input 
                       [ id "chat_window"
                       , attribute "placeholder" "请尬料"
                       , onInput DraftChanged
                       , on "keydown" (ifIsEnter Send)
                       , value model.draft
                       ]
                      [] 
                  ]
            , div [ id "table_area" ]
                  [ h4 [] [ text "Players:"]
                  , div [class "row", id "players"]
                      (List.map
                        (\p ->  div [class "col-sm"]
                           [ text (p.name ++ "(" ++ (String.fromInt p.score) ++ ")")])
                        model.room.players)
                  , h4 [] [text ("牌组还剩：" ++ (String.fromInt game.deck_count) ++"张")]
                  , h4 [id "turn"] [text turnText]
                  , h3 [] [ text "桌面:"]
                  , div [class "row", id "table"] (List.map (makeTableCard model.table_selected) game.table)
                  , hr [] []
                  ]
            , div [id "hand_area"]
                  [ h3 [][text <| "手牌 (" ++ (String.fromInt <| List.length model.hand) ++ "):"]
                  , div [class "mygrid", id "hand"] (List.map (makeCard True model.hand_selected) model.hand)
                  ]
            , controlArea True
            ]

makeTableCard : Set Int -> (String, List Int) -> Html Msg
makeTableCard selectedSet (player_name, cards) =
  let
    width = (50 * (List.length cards) + 50 + max 20 (10 * (String.length player_name)))
  in div
    [ class "player_table",  style "width" <| (String.fromInt width ++ "px")]
    [ div [class "mygrid"]
      <| (List.map (makeCard False selectedSet) cards)
    , span [class "player_name"]
       [text player_name]
    ]



makeCard : Bool -> Set Int -> Int -> Html Msg
makeCard isHand selectedSet cardValue =
  let 
    isSelected = Set.member cardValue selectedSet
    selectEvent = (if isHand then HandSelect else TableSelect)
  in
      div [class "one_card"]
        [ input
              [type_ "checkbox"
              , class (if isHand then "hand_card" else "table_card")
              , attribute "card_id" <| String.fromInt cardValue
              , checked isSelected
              , onCheck (selectEvent cardValue)
              ] []
        , text <| cardText cardValue
        , img [ attribute "height" "120"
              , attribute "src" <| Maybe.withDefault "" <| Array.get (modBy 54 cardValue) cardImgUrls
              , onClick <| (selectEvent cardValue (not isSelected))
              ] []
        ]


controlArea enableMaster =
   div -- control area
      [id "control_area", style "vertical-align" "text-top"]
      [ input [type_ "checkbox", id "auto_end_turn", attribute "checked" ""]
            [text "自动结束回合"]
      , button [ class "turn_control", id "draw", onClick (UI DRAW)]
           [ text "摸牌(v)" ]
      , button [ class "turn_control", id "send",  onClick (UI PLAY)]
            [ text "出牌(b)" ]
      , button [ class "turn_control", id "takeback", onClick (UI TAKE_BACK) ]
            [ text "拿回来" ]
      , button [ class "turn_control", id "return_to_deck", onClick (UI RETURN_TO_DECK) ]
            [ text "放回牌组" ]
      , button [ class "turn_control", id "clear_table", onClick (UI CLEAR_TABLE) ]
            [ text "清空桌面(n)" ]
      , button [ class "turn_control", id "end_turn", onClick (UI END_TURN) ]
            [ text "结束回合" ]
      , button [ id "refresh", onClick (UI REFRESH) ]
            [ text "刷新" ]
      , button [ id "take_turn", onClick (UI TAKE_TURN) ]
            [ text "该我了(m)" ]
      , form [ id "sort_form" ]
            [ span [][ text "主花色" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "S"
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♠" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "H"
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♥" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "D"
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♣" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "C"
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♦" ]
             ]
      ,  if enableMaster then
          div [ class "master", id "master_control" ]
            [ button [ class "master", id "new_game" ]
                [ text "新游戏" ]
            , button [ class "master", id "end_draw" ]
                [ text "停止摸牌" ]
            , button [ class "master", id "spread_cards" ]
                [ text "发牌" ]
            , button [ class "master", id "deal_from_deck" ]
                [ text "翻牌" ]
            , input [ class "master", id "spread_count", placeholder "几张" ]
                []
            ]
          else text ""
      ]


execAction : Model -> Decode.Decoder Model
execAction model =
   (field "action" string) |>
      andThen (\action -> case action of 
          "DRAWED" -> 
            (field "arg" decodeHand) |> 
                andThen (\cards -> Decode.succeed {model | hand = model.hand ++ cards})

          _ -> Decode.fail action
      )


subscriptions : Model -> Sub Msg 
subscriptions _ = messageReceiver Incoming


ifIsEnter msg =
  Decode.field "key" Decode.string
    |> Decode.andThen (\key -> if key == "Enter" then Decode.succeed msg else Decode.fail "some other key")

--TODO
cardText = String.fromInt


cardImgUrls = Array.fromList
    [ "/static/2C.png"
    , "/static/3C.png"
    , "/static/4C.png"
    , "/static/5C.png"
    , "/static/6C.png"
    , "/static/7C.png"
    , "/static/8C.png"
    , "/static/9C.png"
    , "/static/0C.png"
    , "/static/JC.png"
    , "/static/QC.png"
    , "/static/KC.png"
    , "/static/AC.png"
    , "/static/2D.png"
    , "/static/3D.png"
    , "/static/4D.png"
    , "/static/5D.png"
    , "/static/6D.png"
    , "/static/7D.png"
    , "/static/8D.png"
    , "/static/9D.png"
    , "/static/0D.png"
    , "/static/JD.png"
    , "/static/QD.png"
    , "/static/KD.png"
    , "/static/AD.png"
    , "/static/2H.png"
    , "/static/3H.png"
    , "/static/4H.png"
    , "/static/5H.png"
    , "/static/6H.png"
    , "/static/7H.png"
    , "/static/8H.png"
    , "/static/9H.png"
    , "/static/0H.png"
    , "/static/JH.png"
    , "/static/QH.png"
    , "/static/KH.png"
    , "/static/AH.png"
    , "/static/2S.png"
    , "/static/3S.png"
    , "/static/4S.png"
    , "/static/5S.png"
    , "/static/6S.png"
    , "/static/7S.png"
    , "/static/8S.png"
    , "/static/9S.png"
    , "/static/0S.png"
    , "/static/JS.png"
    , "/static/QS.png"
    , "/static/KS.png"
    , "/static/AS.png"
    , "/static/joker.jpg"
    , "/static/XX.png"
    ]

