def recommend_content(learning_data):
    """
    学習データに基づいておすすめコンテンツを生成する関数

    Parameters:
        learning_data (list): 学習ログ [{'question_id': int, 'score': int}, ...]

    Returns:
        list: 推薦コンテンツ [{'question_id': int, 'reason': str}, ...]
    """
    # 簡易的なルールベース推薦 (機械学習モデルに置き換える)
    recommendations = []
    for log in learning_data:
        if log['score'] == 0:  # 間違えた問題を再練習
            recommendations.append({'question_id': log['question_id'], 'reason': 'You struggled with this question.'})
    
    return recommendations
